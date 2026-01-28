from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, decode_token
from models import Roadmap, RoadmapItem, RoadmapDependency, RoadmapAccess, User, Team
from database import db
from flask_bcrypt import generate_password_hash, check_password_hash
from openai import OpenAI
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import uuid
import json
import base64
from typing import Optional, List, Dict
from datetime import datetime

bp_roadmap = Blueprint("roadmap", __name__, url_prefix="/api/roadmap")

# SocketIO будет инициализирован в app.py
socketio = None

def init_socketio(sio_instance):
    """Инициализация SocketIO для использования в blueprint"""
    global socketio
    socketio = sio_instance

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

def _check_roadmap_access(roadmap: Roadmap, user_id: int, require_edit: bool = False) -> bool:
    """Проверка доступа пользователя к дорожной карте"""
    if roadmap.creator_id == user_id:
        return True
    
    access = RoadmapAccess.query.filter_by(roadmap_id=roadmap.id, user_id=user_id).first()
    if not access:
        return False
    
    if require_edit and access.access_level not in ['editor', 'owner']:
        return False
    
    return True

def _broadcast_to_roadmap(roadmap_id: int, event: str, data: dict):
    """Отправка события через WebSocket всем пользователям, подключенным к дорожной карте"""
    if socketio:
        room = f"roadmap_{roadmap_id}"
        socketio.emit(event, data, room=room)

# ========== Roadmap CRUD ==========

@bp_roadmap.route("", methods=["POST"])
@jwt_required()
def create_roadmap():
    """Создание новой дорожной карты"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        name = data.get("name", "").strip()
        
        if not name:
            return jsonify({"error": "Название карты обязательно"}), 400
        
        roadmap = Roadmap(
            name=name,
            creator_id=user_id
        )
        
        db.session.add(roadmap)
        db.session.commit()
        
        # Создаем доступ для создателя
        access = RoadmapAccess(
            roadmap_id=roadmap.id,
            user_id=user_id,
            access_level='owner'
        )
        db.session.add(access)
        db.session.commit()
        
        try:
            quarter_start = getattr(roadmap, 'quarter_start', None)
            sprints_per_quarter = getattr(roadmap, 'sprints_per_quarter', None) or 6
        except AttributeError:
            quarter_start = None
            sprints_per_quarter = 6
        
        return jsonify({
            "id": roadmap.id,
            "name": roadmap.name,
            "creator_id": roadmap.creator_id,
            "quarter_start": quarter_start,
            "sprints_per_quarter": sprints_per_quarter,
            "created_at": roadmap.created_at.isoformat(),
            "access_token": roadmap.access_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"Ошибка создания карты: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@bp_roadmap.route("", methods=["GET"])
@jwt_required()
def list_roadmaps():
    """Список дорожных карт пользователя"""
    try:
        user_id = int(get_jwt_identity())
        
        # Проверяем, существуют ли новые колонки в БД
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('roadmap')]
        has_quarter_start = 'quarter_start' in columns
        has_sprints_per_quarter = 'sprints_per_quarter' in columns
        
        # Получаем карты, где пользователь создатель или имеет доступ
        # Используем raw SQL, если колонок нет
        if not has_quarter_start or not has_sprints_per_quarter:
            # Используем raw SQL запрос без новых колонок
            result = db.session.execute(text("""
                SELECT r.id, r.name, r.creator_id, r.created_at, r.updated_at,
                       COUNT(ri.id) as item_count
                FROM roadmap r
                LEFT JOIN roadmap_item ri ON ri.roadmap_id = r.id
                WHERE r.creator_id = :user_id
                   OR r.id IN (
                       SELECT roadmap_id FROM roadmap_access WHERE user_id = :user_id
                   )
                GROUP BY r.id, r.name, r.creator_id, r.created_at, r.updated_at
            """), {"user_id": user_id})
            
            roadmaps_list = []
            for row in result:
                roadmaps_list.append({
                    "id": row.id,
                    "name": row.name,
                    "creator_id": row.creator_id,
                    "quarter_start": None,
                    "sprints_per_quarter": 6,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                    "item_count": row.item_count or 0
                })
            
            return jsonify(roadmaps_list), 200
        else:
            # Используем обычный ORM запрос
            created_roadmaps = Roadmap.query.filter_by(creator_id=user_id).all()
            accessed_roadmaps = db.session.query(Roadmap).join(RoadmapAccess).filter(
                RoadmapAccess.user_id == user_id
            ).all()
            
            all_roadmaps = list(set(created_roadmaps + accessed_roadmaps))
            
            result = []
            for roadmap in all_roadmaps:
                result.append({
                    "id": roadmap.id,
                    "name": roadmap.name,
                    "creator_id": roadmap.creator_id,
                    "quarter_start": roadmap.quarter_start,
                    "sprints_per_quarter": roadmap.sprints_per_quarter or 6,
                    "created_at": roadmap.created_at.isoformat(),
                    "updated_at": roadmap.updated_at.isoformat(),
                    "item_count": len(roadmap.items)
                })
            
            return jsonify(result), 200
        
    except Exception as e:
        import traceback
        print(f"Ошибка загрузки списка карт: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@bp_roadmap.route("/<int:roadmap_id>", methods=["GET"])
@jwt_required()
def get_roadmap(roadmap_id):
    """Получение дорожной карты со всеми элементами и зависимостями"""
    try:
        user_id = int(get_jwt_identity())
        roadmap = Roadmap.query.get(roadmap_id)
        
        if not roadmap:
            return jsonify({"error": "Дорожная карта не найдена"}), 404
        
        if not _check_roadmap_access(roadmap, user_id):
            return jsonify({"error": "Нет доступа к этой дорожной карте"}), 403
        
        # Получаем все элементы
        items = []
        for item in roadmap.items:
            items.append({
                "id": item.id,
                "type": item.type,
                "title": item.title,
                "description": item.description,
                "position_x": item.position_x,
                "position_y": item.position_y,
                "team_id": item.team_id,
                "metadata": item.item_metadata or {},
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat()
            })
        
        # Получаем все зависимости
        dependencies = []
        for item in roadmap.items:
            for dep in item.dependencies_from:
                dependencies.append({
                    "id": dep.id,
                    "from_item_id": dep.from_item_id,
                    "to_item_id": dep.to_item_id,
                    "dependency_type": dep.dependency_type,
                    "created_at": dep.created_at.isoformat()
                })
        
        try:
            quarter_start = getattr(roadmap, 'quarter_start', None)
            sprints_per_quarter = getattr(roadmap, 'sprints_per_quarter', None) or 6
        except AttributeError:
            quarter_start = None
            sprints_per_quarter = 6
        
        return jsonify({
            "id": roadmap.id,
            "name": roadmap.name,
            "creator_id": roadmap.creator_id,
            "quarter_start": quarter_start,
            "sprints_per_quarter": sprints_per_quarter,
            "created_at": roadmap.created_at.isoformat(),
            "updated_at": roadmap.updated_at.isoformat(),
            "items": items,
            "dependencies": dependencies
        }), 200
        
    except Exception as e:
        import traceback
        print(f"Ошибка загрузки карты: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@bp_roadmap.route("/<int:roadmap_id>", methods=["PUT"])
@jwt_required()
def update_roadmap(roadmap_id):
    """Обновление дорожной карты"""
    try:
        user_id = int(get_jwt_identity())
        roadmap = Roadmap.query.get(roadmap_id)
        
        if not roadmap:
            return jsonify({"error": "Дорожная карта не найдена"}), 404
        
        if not _check_roadmap_access(roadmap, user_id, require_edit=True):
            return jsonify({"error": "Нет прав на редактирование"}), 403
        
        data = request.get_json() or {}
        if "name" in data:
            roadmap.name = data["name"].strip()
        if "quarter_start" in data:
            roadmap.quarter_start = data["quarter_start"]
        if "sprints_per_quarter" in data:
            roadmap.sprints_per_quarter = data["sprints_per_quarter"]
        
        roadmap.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "id": roadmap.id,
            "name": roadmap.name,
            "quarter_start": roadmap.quarter_start,
            "sprints_per_quarter": roadmap.sprints_per_quarter,
            "updated_at": roadmap.updated_at.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp_roadmap.route("/<int:roadmap_id>", methods=["DELETE"])
@jwt_required()
def delete_roadmap(roadmap_id):
    """Удаление дорожной карты"""
    try:
        user_id = int(get_jwt_identity())
        roadmap = Roadmap.query.get(roadmap_id)
        
        if not roadmap:
            return jsonify({"error": "Дорожная карта не найдена"}), 404
        
        if roadmap.creator_id != user_id:
            return jsonify({"error": "Только создатель может удалить карту"}), 403
        
        db.session.delete(roadmap)
        db.session.commit()
        
        return jsonify({"message": "Дорожная карта удалена"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ========== Access Management ==========

@bp_roadmap.route("/<int:roadmap_id>/share", methods=["POST"])
@jwt_required()
def create_share_link(roadmap_id):
    """Создание ссылки для доступа с паролем"""
    try:
        user_id = int(get_jwt_identity())
        roadmap = Roadmap.query.get(roadmap_id)
        
        if not roadmap:
            return jsonify({"error": "Дорожная карта не найдена"}), 404
        
        if not _check_roadmap_access(roadmap, user_id, require_edit=True):
            return jsonify({"error": "Нет прав на редактирование"}), 403
        
        data = request.get_json() or {}
        password = data.get("password", "").strip()
        
        # Генерируем токен доступа
        access_token = str(uuid.uuid4())
        roadmap.access_token = access_token
        
        # Устанавливаем пароль
        if password:
            roadmap.set_password(password)
        else:
            roadmap.password_hash = None
        
        roadmap.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "access_token": access_token,
            "share_url": f"/roadmap/shared/{access_token}",
            "has_password": bool(password)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp_roadmap.route("/shared/<access_token>", methods=["GET"])
def get_roadmap_by_token(access_token):
    """Получение дорожной карты по токену (без пароля - только проверка существования)"""
    try:
        roadmap = Roadmap.query.filter_by(access_token=access_token).first()
        
        if not roadmap:
            return jsonify({"error": "Дорожная карта не найдена"}), 404
        
        return jsonify({
            "id": roadmap.id,
            "name": roadmap.name,
            "has_password": bool(roadmap.password_hash)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp_roadmap.route("/shared/<access_token>/access", methods=["POST"])
def verify_password_and_get_roadmap(access_token):
    """Проверка пароля и получение полных данных карты"""
    try:
        roadmap = Roadmap.query.filter_by(access_token=access_token).first()
        
        if not roadmap:
            return jsonify({"error": "Дорожная карта не найдена"}), 404
        
        data = request.get_json() or {}
        password = data.get("password", "")
        
        # Проверяем пароль, если он установлен
        if roadmap.password_hash:
            if not roadmap.check_password(password):
                return jsonify({"error": "Неверный пароль"}), 401
        
        # Получаем все элементы
        items = []
        for item in roadmap.items:
            items.append({
                "id": item.id,
                "type": item.type,
                "title": item.title,
                "description": item.description,
                "position_x": item.position_x,
                "position_y": item.position_y,
                "team_id": item.team_id,
                "metadata": item.item_metadata or {},
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat()
            })
        
        # Получаем все зависимости
        dependencies = []
        for item in roadmap.items:
            for dep in item.dependencies_from:
                dependencies.append({
                    "id": dep.id,
                    "from_item_id": dep.from_item_id,
                    "to_item_id": dep.to_item_id,
                    "dependency_type": dep.dependency_type,
                    "created_at": dep.created_at.isoformat()
                })
        
        try:
            quarter_start = getattr(roadmap, 'quarter_start', None)
            sprints_per_quarter = getattr(roadmap, 'sprints_per_quarter', None) or 6
        except AttributeError:
            quarter_start = None
            sprints_per_quarter = 6
        
        return jsonify({
            "id": roadmap.id,
            "name": roadmap.name,
            "creator_id": roadmap.creator_id,
            "quarter_start": quarter_start,
            "sprints_per_quarter": sprints_per_quarter,
            "created_at": roadmap.created_at.isoformat(),
            "updated_at": roadmap.updated_at.isoformat(),
            "items": items,
            "dependencies": dependencies
        }), 200
        
    except Exception as e:
        import traceback
        print(f"Ошибка загрузки карты по токену: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# ========== Roadmap Items CRUD ==========

@bp_roadmap.route("/<int:roadmap_id>/item", methods=["POST"])
@jwt_required()
def create_item(roadmap_id):
    """Создание элемента дорожной карты"""
    try:
        user_id = int(get_jwt_identity())
        roadmap = Roadmap.query.get(roadmap_id)
        
        if not roadmap:
            return jsonify({"error": "Дорожная карта не найдена"}), 404
        
        if not _check_roadmap_access(roadmap, user_id, require_edit=True):
            return jsonify({"error": "Нет прав на редактирование"}), 403
        
        data = request.get_json() or {}
        item_type = data.get("type", "story")
        title = data.get("title", "").strip()
        description = data.get("description", "").strip()
        position_x = data.get("position_x", 0.0)
        position_y = data.get("position_y", 0.0)
        team_id = data.get("team_id")
        metadata = data.get("metadata", {})
        
        if not title:
            return jsonify({"error": "Название элемента обязательно"}), 400
        
        if item_type not in ["epic", "story"]:
            return jsonify({"error": "Тип должен быть 'epic' или 'story'"}), 400
        
        # Проверяем существование команды, если указана
        if team_id:
            team = Team.query.get(team_id)
            if not team:
                return jsonify({"error": f"Команда с ID {team_id} не найдена"}), 400
        
        item = RoadmapItem(
            roadmap_id=roadmap_id,
            type=item_type,
            title=title,
            description=description,
            position_x=position_x,
            position_y=position_y,
            team_id=team_id if team_id else None,
            item_metadata=metadata
        )
        
        db.session.add(item)
        roadmap.updated_at = datetime.utcnow()
        db.session.commit()
        
        item_data = {
            "id": item.id,
            "type": item.type,
            "title": item.title,
            "description": item.description,
            "position_x": item.position_x,
            "position_y": item.position_y,
            "team_id": item.team_id,
            "metadata": item.item_metadata or {},
            "created_at": item.created_at.isoformat()
        }
        
        # Отправляем событие через WebSocket
        _broadcast_to_roadmap(roadmap_id, "item_create", item_data)
        
        return jsonify(item_data), 201
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"Ошибка создания элемента: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@bp_roadmap.route("/<int:roadmap_id>/item/<int:item_id>", methods=["PUT"])
@jwt_required()
def update_item(roadmap_id, item_id):
    """Обновление элемента дорожной карты"""
    try:
        user_id = int(get_jwt_identity())
        roadmap = Roadmap.query.get(roadmap_id)
        
        if not roadmap:
            return jsonify({"error": "Дорожная карта не найдена"}), 404
        
        if not _check_roadmap_access(roadmap, user_id, require_edit=True):
            return jsonify({"error": "Нет прав на редактирование"}), 403
        
        item = RoadmapItem.query.filter_by(id=item_id, roadmap_id=roadmap_id).first()
        if not item:
            return jsonify({"error": "Элемент не найден"}), 404
        
        data = request.get_json() or {}
        
        if "title" in data:
            item.title = data["title"].strip()
        if "description" in data:
            item.description = data["description"].strip()
        if "type" in data:
            if data["type"] in ["epic", "story"]:
                item.type = data["type"]
        if "position_x" in data:
            item.position_x = float(data["position_x"])
        if "position_y" in data:
            item.position_y = float(data["position_y"])
        if "team_id" in data:
            team_id = data["team_id"]
            if team_id:
                team = Team.query.get(team_id)
                if not team:
                    return jsonify({"error": f"Команда с ID {team_id} не найдена"}), 400
                item.team_id = team_id
            else:
                item.team_id = None
        if "metadata" in data:
            item.item_metadata = data["metadata"]
        
        item.updated_at = datetime.utcnow()
        roadmap.updated_at = datetime.utcnow()
        db.session.commit()
        
        item_data = {
            "id": item.id,
            "type": item.type,
            "title": item.title,
            "description": item.description,
            "position_x": item.position_x,
            "position_y": item.position_y,
            "team_id": item.team_id,
            "metadata": item.item_metadata or {},
            "updated_at": item.updated_at.isoformat()
        }
        
        # Отправляем событие через WebSocket
        _broadcast_to_roadmap(roadmap_id, "item_update", item_data)
        
        return jsonify(item_data), 200
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"Ошибка обновления элемента: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@bp_roadmap.route("/<int:roadmap_id>/item/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete_item(roadmap_id, item_id):
    """Удаление элемента дорожной карты"""
    try:
        user_id = int(get_jwt_identity())
        roadmap = Roadmap.query.get(roadmap_id)
        
        if not roadmap:
            return jsonify({"error": "Дорожная карта не найдена"}), 404
        
        if not _check_roadmap_access(roadmap, user_id, require_edit=True):
            return jsonify({"error": "Нет прав на редактирование"}), 403
        
        item = RoadmapItem.query.filter_by(id=item_id, roadmap_id=roadmap_id).first()
        if not item:
            return jsonify({"error": "Элемент не найден"}), 404
        
        item_id = item.id
        db.session.delete(item)
        roadmap.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Отправляем событие через WebSocket
        _broadcast_to_roadmap(roadmap_id, "item_delete", {"id": item_id})
        
        return jsonify({"message": "Элемент удален"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ========== Dependencies CRUD ==========

@bp_roadmap.route("/<int:roadmap_id>/dependency", methods=["POST"])
@jwt_required()
def create_dependency(roadmap_id):
    """Создание зависимости между элементами"""
    try:
        user_id = int(get_jwt_identity())
        roadmap = Roadmap.query.get(roadmap_id)
        
        if not roadmap:
            return jsonify({"error": "Дорожная карта не найдена"}), 404
        
        if not _check_roadmap_access(roadmap, user_id, require_edit=True):
            return jsonify({"error": "Нет прав на редактирование"}), 403
        
        data = request.get_json() or {}
        from_item_id = data.get("from_item_id")
        to_item_id = data.get("to_item_id")
        dependency_type = data.get("dependency_type", "depends_on")
        
        if not from_item_id or not to_item_id:
            return jsonify({"error": "from_item_id и to_item_id обязательны"}), 400
        
        valid_types = ["blocks", "depends_on", "related_to", "requires", "precedes", "follows"]
        if dependency_type not in valid_types:
            return jsonify({"error": f"Тип зависимости должен быть одним из: {', '.join(valid_types)}"}), 400
        
        # Проверяем, что элементы принадлежат этой карте
        from_item = RoadmapItem.query.filter_by(id=from_item_id, roadmap_id=roadmap_id).first()
        to_item = RoadmapItem.query.filter_by(id=to_item_id, roadmap_id=roadmap_id).first()
        
        if not from_item or not to_item:
            return jsonify({"error": "Один или оба элемента не найдены"}), 404
        
        if from_item_id == to_item_id:
            return jsonify({"error": "Элемент не может зависеть от самого себя"}), 400
        
        # Проверяем, нет ли уже такой зависимости
        existing = RoadmapDependency.query.filter_by(
            from_item_id=from_item_id,
            to_item_id=to_item_id
        ).first()
        
        if existing:
            return jsonify({"error": "Зависимость уже существует"}), 409
        
        dependency = RoadmapDependency(
            from_item_id=from_item_id,
            to_item_id=to_item_id,
            dependency_type=dependency_type
        )
        
        db.session.add(dependency)
        roadmap.updated_at = datetime.utcnow()
        db.session.commit()
        
        dep_data = {
            "id": dependency.id,
            "from_item_id": dependency.from_item_id,
            "to_item_id": dependency.to_item_id,
            "dependency_type": dependency.dependency_type,
            "created_at": dependency.created_at.isoformat()
        }
        
        # Отправляем событие через WebSocket
        _broadcast_to_roadmap(roadmap_id, "dependency_create", dep_data)
        
        return jsonify(dep_data), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp_roadmap.route("/<int:roadmap_id>/dependency/<int:dep_id>", methods=["DELETE"])
@jwt_required()
def delete_dependency(roadmap_id, dep_id):
    """Удаление зависимости"""
    try:
        user_id = int(get_jwt_identity())
        roadmap = Roadmap.query.get(roadmap_id)
        
        if not roadmap:
            return jsonify({"error": "Дорожная карта не найдена"}), 404
        
        if not _check_roadmap_access(roadmap, user_id, require_edit=True):
            return jsonify({"error": "Нет прав на редактирование"}), 403
        
        # Проверяем, что зависимость принадлежит элементу этой карты
        dependency = db.session.query(RoadmapDependency).join(
            RoadmapItem, RoadmapDependency.from_item_id == RoadmapItem.id
        ).filter(
            RoadmapDependency.id == dep_id,
            RoadmapItem.roadmap_id == roadmap_id
        ).first()
        
        if not dependency:
            return jsonify({"error": "Зависимость не найдена"}), 404
        
        dep_id = dependency.id
        db.session.delete(dependency)
        roadmap.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Отправляем событие через WebSocket
        _broadcast_to_roadmap(roadmap_id, "dependency_delete", {"id": dep_id})
        
        return jsonify({"message": "Зависимость удалена"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ========== AI Image Parsing ==========

def _parse_image_with_ai(image_file) -> List[Dict]:
    """Распознавание эпиков и историй из изображения через OpenAI Vision API"""
    client = get_openai_client()
    if not client:
        raise Exception("OpenAI API key not configured")
    
    # Читаем изображение
    image_data = image_file.read()
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    prompt = """Проанализируй это изображение дорожной карты или бэклога. 
Извлеки все эпики и истории (user stories), которые видишь на изображении.

Для каждого элемента определи:
- Тип: "epic" или "story"
- Название (title)
- Описание (description), если есть
- Команду (team), если указана

Верни результат в формате JSON со следующей структурой:
{
  "items": [
    {
      "type": "epic" или "story",
      "title": "Название",
      "description": "Описание или пустая строка",
      "team": "Название команды или null"
    }
  ]
}

Важно: верни ТОЛЬКО валидный JSON, без markdown разметки, без дополнительного текста."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        return result.get("items", [])
        
    except Exception as e:
        raise Exception(f"Ошибка при распознавании изображения: {str(e)}")

@bp_roadmap.route("/<int:roadmap_id>/upload-image", methods=["POST"])
@jwt_required()
def upload_image(roadmap_id):
    """Загрузка изображения и автоматическое создание элементов через AI"""
    try:
        user_id = int(get_jwt_identity())
        roadmap = Roadmap.query.get(roadmap_id)
        
        if not roadmap:
            return jsonify({"error": "Дорожная карта не найдена"}), 404
        
        if not _check_roadmap_access(roadmap, user_id, require_edit=True):
            return jsonify({"error": "Нет прав на редактирование"}), 403
        
        if 'image' not in request.files:
            return jsonify({"error": "Изображение не загружено"}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({"error": "Файл не выбран"}), 400
        
        # Распознаем изображение через AI
        try:
            parsed_items = _parse_image_with_ai(image_file)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
        # Получаем список команд для маппинга названий
        teams = Team.query.filter_by(user_id=user_id).all()
        team_map = {team.name: team.id for team in teams}
        
        # Создаем элементы
        created_items = []
        start_x = 100.0
        start_y = 100.0
        spacing = 200.0
        
        for idx, item_data in enumerate(parsed_items):
            item_type = item_data.get("type", "story")
            title = item_data.get("title", "").strip()
            description = item_data.get("description", "").strip()
            team_name = item_data.get("team")
            team_id = team_map.get(team_name) if team_name else None
            
            if not title:
                continue
            
            # Располагаем элементы в сетке
            row = idx // 3
            col = idx % 3
            position_x = start_x + col * spacing
            position_y = start_y + row * spacing
            
            item = RoadmapItem(
                roadmap_id=roadmap_id,
                type=item_type,
                title=title,
                description=description,
                position_x=position_x,
                position_y=position_y,
                team_id=team_id,
                item_metadata={"source": "ai_image_parsing"}
            )
            
            db.session.add(item)
            created_items.append({
                "id": item.id,
                "type": item.type,
                "title": item.title,
                "description": item.description,
                "position_x": item.position_x,
                "position_y": item.position_y,
                "team_id": item.team_id
            })
        
        roadmap.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Отправляем события для всех созданных элементов
        for item_data in created_items:
            _broadcast_to_roadmap(roadmap_id, "item_create", item_data)
        
        return jsonify({
            "message": f"Создано элементов: {len(created_items)}",
            "items": created_items
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ========== WebSocket Handlers ==========

def register_socketio_handlers(sio):
    """Регистрация WebSocket обработчиков"""
    
    @sio.on('connect')
    def handle_connect(auth):
        """Обработка подключения к WebSocket"""
        try:
            auth = auth or {}
            token = auth.get('token')
            roadmap_id = auth.get('roadmap_id')
            access_token = auth.get('access_token')
            
            if not roadmap_id:
                return False
            
            # Проверяем доступ к дорожной карте
            roadmap = Roadmap.query.get(roadmap_id)
            if not roadmap:
                return False
            
            # Проверяем доступ (для shared карт проверяем через access_token)
            if access_token:
                if roadmap.access_token != access_token:
                    return False
                # Для shared карт проверяем пароль, если установлен
                password = auth.get('password')
                if roadmap.password_hash:
                    if not password or not roadmap.check_password(password):
                        return False
            else:
                # Для авторизованных пользователей
                if not token:
                    return False
                try:
                    decoded = decode_token(token)
                    user_id = int(decoded['sub'])
                except:
                    return False
                
                if not _check_roadmap_access(roadmap, user_id):
                    return False
            
            # Подключаемся к комнате
            join_room(f"roadmap_{roadmap_id}")
            return True
            
        except Exception as e:
            print(f"WebSocket connect error: {e}")
            return False
    
    @sio.on('disconnect')
    def handle_disconnect():
        """Обработка отключения от WebSocket"""
        pass
    
    @sio.on('item_move')
    def handle_item_move(data):
        """Обработка перемещения элемента"""
        try:
            roadmap_id = data.get('roadmap_id')
            item_id = data.get('item_id')
            position_x = data.get('position_x')
            position_y = data.get('position_y')
            
            if not all([roadmap_id, item_id, position_x is not None, position_y is not None]):
                return
            
            roadmap = Roadmap.query.get(roadmap_id)
            if not roadmap:
                return
            
            item = RoadmapItem.query.filter_by(id=item_id, roadmap_id=roadmap_id).first()
            if not item:
                return
            
            item.position_x = float(position_x)
            item.position_y = float(position_y)
            item.updated_at = datetime.utcnow()
            roadmap.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Отправляем обновление всем, кроме отправителя
            emit('item_move', {
                'item_id': item_id,
                'position_x': item.position_x,
                'position_y': item.position_y
            }, room=f"roadmap_{roadmap_id}", include_self=False)
            
        except Exception as e:
            print(f"WebSocket item_move error: {e}")
            db.session.rollback()
