import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const pkg = require('../apps/web/package.json');

(async () => {
  try {
    const { createClient } = await import('@supabase/supabase-js');
    const SUPABASE_URL = 'http://127.0.0.1:54321';
    const ANON_KEY = process.env.SUPABASE_ANON_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'anon';
    const token = process.env.TOKEN;
    if (!token) {
      console.error('TOKEN env var is required');
      process.exit(2);
    }
    const supabase = createClient(SUPABASE_URL, ANON_KEY, {
      auth: { persistSession: false, autoRefreshToken: false },
    });
    // set auth token
    if (typeof supabase.auth.setAuth === 'function') {
      supabase.auth.setAuth(token);
    } else if (supabase.auth && typeof supabase.auth.api === 'object' && typeof supabase.auth.api.setAuth === 'function') {
      supabase.auth.api.setAuth(token);
    }
    console.log('Listing factors...');
    const factors = await supabase.auth.mfa.listFactors();
    console.log('factors result:', JSON.stringify(factors, null, 2));
    if (factors.error) process.exit(0);
    const verified = await supabase.auth.mfa.getAuthenticatorAssuranceLevel();
    console.log('assurance:', JSON.stringify(verified, null, 2));
  } catch (err) {
    console.error('probe error', err);
    process.exit(1);
  }
})();
