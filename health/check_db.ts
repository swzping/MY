import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
dotenv.config();

const supabaseUrl = process.env.VITE_SUPABASE_URL || '';
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY || '';

const supabase = createClient(supabaseUrl, supabaseKey);

async function checkDb() {
  console.log('Checking database connection...');
  const { data, error } = await supabase.from('users').select('count').limit(1);
  if (error) {
    console.error('Error connecting to database:', error);
  } else {
    console.log('Database connection successful. Users table exists.');
  }
}

checkDb();
