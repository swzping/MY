-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    birth_date DATE,
    gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'other')),
    height FLOAT CHECK (height > 0 AND height < 300),
    weight FLOAT CHECK (weight > 0 AND weight < 500),
    health_profile JSONB DEFAULT '{}',
    member_type VARCHAR(20) DEFAULT 'free' CHECK (member_type IN ('free', 'premium', 'professional')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for users
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_member_type ON users(member_type);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for users
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create constitution_results table
CREATE TABLE IF NOT EXISTS constitution_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    test_id UUID NOT NULL,
    constitution_type VARCHAR(50) NOT NULL,
    score FLOAT CHECK (score >= 0 AND score <= 100),
    characteristics JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, test_id)
);

-- Create indexes for constitution_results
CREATE INDEX IF NOT EXISTS idx_constitution_results_user_id ON constitution_results(user_id);
CREATE INDEX IF NOT EXISTS idx_constitution_results_constitution_type ON constitution_results(constitution_type);
CREATE INDEX IF NOT EXISTS idx_constitution_results_created_at ON constitution_results(created_at DESC);

-- Create diet_records table
CREATE TABLE IF NOT EXISTS diet_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meal_date DATE NOT NULL,
    meal_type VARCHAR(20) CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')),
    food_items JSONB NOT NULL DEFAULT '[]',
    nutrition_data JSONB DEFAULT '{}',
    image_url VARCHAR(500),
    health_score FLOAT CHECK (health_score >= 0 AND health_score <= 100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for diet_records
CREATE INDEX IF NOT EXISTS idx_diet_records_user_id ON diet_records(user_id);
CREATE INDEX IF NOT EXISTS idx_diet_records_meal_date ON diet_records(meal_date);
CREATE INDEX IF NOT EXISTS idx_diet_records_meal_type ON diet_records(meal_type);

-- Create exercise_data table
CREATE TABLE IF NOT EXISTS exercise_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exercise_date DATE NOT NULL,
    exercise_type VARCHAR(100) NOT NULL,
    duration_minutes INTEGER CHECK (duration_minutes > 0),
    calories_burned FLOAT CHECK (calories_burned >= 0),
    metrics JSONB DEFAULT '{}',
    heart_rate_avg INTEGER,
    heart_rate_max INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for exercise_data
CREATE INDEX IF NOT EXISTS idx_exercise_data_user_id ON exercise_data(user_id);
CREATE INDEX IF NOT EXISTS idx_exercise_data_exercise_date ON exercise_data(exercise_date);
CREATE INDEX IF NOT EXISTS idx_exercise_data_exercise_type ON exercise_data(exercise_type);

-- Create ai_chat_history table
CREATE TABLE IF NOT EXISTS ai_chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(100) NOT NULL,
    messages JSONB NOT NULL DEFAULT '[]',
    chat_type VARCHAR(50) DEFAULT 'health_consultation',
    ai_model VARCHAR(100),
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for ai_chat_history
CREATE INDEX IF NOT EXISTS idx_ai_chat_user_id ON ai_chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_chat_session_id ON ai_chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_chat_created_at ON ai_chat_history(created_at DESC);

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE constitution_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE diet_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE exercise_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_chat_history ENABLE ROW LEVEL SECURITY;

-- Grant permissions (adjust as needed for your specific role usage)
GRANT SELECT, INSERT, UPDATE, DELETE ON users TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON constitution_results TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON diet_records TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON exercise_data TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ai_chat_history TO service_role;

-- Allow public access for now (for development convenience if not using service role)
-- WARNING: Tighten this in production!
CREATE POLICY "Allow all access for service role" ON users FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access for service role" ON constitution_results FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access for service role" ON diet_records FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access for service role" ON exercise_data FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access for service role" ON ai_chat_history FOR ALL TO service_role USING (true) WITH CHECK (true);
