import { useState } from 'react';
import { AssistantPage } from '../pages/AssistantPage';
import { LoginPage } from '../pages/LoginPage';
import { hasToken } from '../stores/session';
export function App() { const [authenticated, setAuthenticated] = useState(hasToken()); return authenticated ? <AssistantPage /> : <LoginPage onLogin={() => setAuthenticated(true)} />; }
