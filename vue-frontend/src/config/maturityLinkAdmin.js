/**
 * Доступ к агрегированному дашборду maturity link.
 * Базовые email + VUE_APP_MATURITY_LINK_ADMIN_EMAILS (через запятую) при сборке.
 * На сервере список расширяется через MATURITY_LINK_ADMIN_EMAILS — держите в sync с maturity_link.py
 */
const DEFAULT_EMAILS = ['artem@onagile.ru', 'artjoms.grinakins@gmail.com'];

const envExtra =
  typeof process !== 'undefined' && process.env.VUE_APP_MATURITY_LINK_ADMIN_EMAILS
    ? process.env.VUE_APP_MATURITY_LINK_ADMIN_EMAILS.split(',')
        .map((e) => e.trim().toLowerCase())
        .filter(Boolean)
    : [];

export const MATURITY_LINK_ADMIN_EMAILS = Object.freeze(
  [...new Set([...DEFAULT_EMAILS.map((e) => e.toLowerCase()), ...envExtra])]
);

const SET = new Set(MATURITY_LINK_ADMIN_EMAILS);

export function isMaturityLinkAdminEmail(usernameOrEmail) {
  if (!usernameOrEmail || typeof usernameOrEmail !== 'string') return false;
  return SET.has(usernameOrEmail.trim().toLowerCase());
}
