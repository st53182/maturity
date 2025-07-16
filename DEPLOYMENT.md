# Avatar Migration Deployment Instructions

## Production Database Migration

### Step 1: Connect to PostgreSQL Database
1. Log in to render.com with credentials: artjoms.grinakins@gmail.com / Mi2301dd4545
2. Navigate to the "scrum-db" PostgreSQL database
3. Open pgAdmin4 or database connection tool

### Step 2: Run Migration Script
1. Open the `avatar_migration.sql` file in pgAdmin4
2. Execute the script to add the avatar column:
   ```sql
   -- The script will:
   -- 1. Add avatar column with default value 'default.png'
   -- 2. Update existing records to have the default avatar
   -- 3. Verify the migration completed successfully
   ```

### Step 3: Verify Migration
After running the script, verify the changes:
```sql
-- Check table schema
\d employee

-- Verify avatar column exists and has data
SELECT id, name, avatar FROM employee LIMIT 5;

-- Count records with avatar
SELECT COUNT(*) as total_employees, 
       COUNT(avatar) as employees_with_avatar 
FROM employee;
```

## Application Deployment

### Automatic Deployment
The application code includes backward compatibility and will be automatically deployed via render.com autodeploy when changes are pushed to GitHub.

### Manual Verification
After deployment, test the endpoints:
1. Visit https://growboard.ru/
2. Navigate to "Сотрудники & Мотивация" section
3. Verify employees are visible (no longer missing)
4. Test avatar selection functionality

### Troubleshooting
If issues persist after migration:
1. Check render.com logs for any remaining errors
2. Verify the avatar column was added successfully
3. Ensure all existing employees have avatar values

## Technical Details

### Database Changes
- Added `avatar VARCHAR(50) DEFAULT 'default.png'` column to employee table
- Updated existing records to have default avatar value
- Used `IF NOT EXISTS` to make migration safe for repeated runs

### Code Changes
- Added `safe_avatar` property to Employee model for backward compatibility
- Updated all API endpoints to use safe avatar access
- Added try/catch blocks around avatar assignment operations

### Backward Compatibility
The code now handles both scenarios:
- New installations: avatar column exists from the start
- Existing installations: gracefully handles missing avatar column until migration is run
