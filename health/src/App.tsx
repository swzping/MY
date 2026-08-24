import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/MainLayout';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import TCMPage from './pages/TCMPage';
import NutritionPage from './pages/NutritionPage';
import MentalHealthPage from './pages/MentalHealthPage';
import FitnessPage from './pages/FitnessPage';
import AssessmentPage from './pages/AssessmentPage';
import Profile from './pages/Profile';
import NotFound from './pages/NotFound';
import RequireAuth from './components/RequireAuth';
import { supabase } from './lib/supabase';

const App: React.FC = () => {
  const [session, setSession] = React.useState<any>(null);

  React.useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        <Route path="/" element={<RequireAuth><MainLayout /></RequireAuth>}>
          <Route index element={<Home />} />
          <Route path="tcm" element={<TCMPage />} />
          <Route path="nutrition" element={<NutritionPage />} />
          <Route path="mental" element={<MentalHealthPage />} />
          <Route path="fitness" element={<FitnessPage />} />
          <Route path="assessment" element={<AssessmentPage />} />
          <Route path="profile" element={<Profile />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  );
};

export default App;
