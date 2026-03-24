/**
 * Доступ к агрегированному дашборду maturity link.
 * Держать в sync с MATURITY_LINK_ADMIN_EMAILS в maturity_link.py
 */
export const MATURITY_LINK_ADMIN_EMAILS = Object.freeze([
  'artem@onagile.ru',
  'artjoms.grinakins@gmail.com',
]);

const SET = new Set(MATURITY_LINK_ADMIN_EMAILS.map((e) => e.toLowerCase()));

export function isMaturityLinkAdminEmail(usernameOrEmail) {
  if (!usernameOrEmail || typeof usernameOrEmail !== 'string') return false;
  return SET.has(usernameOrEmail.trim().toLowerCase());
}
