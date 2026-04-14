export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    const { initDB } = await import('./lib/db.js');
    await initDB();
  }
}
