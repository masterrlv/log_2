import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Container,
  Paper,
  TextInput,
  PasswordInput,
  Button,
  Title,
  Text,
  Anchor,
  Alert,
  LoadingOverlay,
  Select,
} from '@mantine/core';
import { IconAlertCircle } from '@tabler/icons-react';

export function RegisterPage() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'viewer' | 'admin'>('viewer');
  const { register, error, loading } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await register(username, email, password);
      navigate('/dashboard');
    } catch (err) {
      // Error is handled by the auth context
    }
  };

  return (
    <Container size={420} my={40}>
      <Title align="center" sx={{ fontWeight: 900 }}>
        Create an account
      </Title>
      <Text color="dimmed" size="sm" align="center" mt={5}>
        Already have an account?{' '}
        <Anchor component={Link} to="/login" size="sm">
          Sign in
        </Anchor>
      </Text>

      <Paper withBorder shadow="md" p={30} mt={30} radius="md" pos="relative">
        <LoadingOverlay visible={loading} overlayBlur={2} />
        
        {error && (
          <Alert icon={<IconAlertCircle size={16} />} title="Error!" color="red" mb="md">
            {error}
          </Alert>
        )}
        
        <form onSubmit={handleSubmit}>
          <TextInput
            label="Username"
            placeholder="Your username"
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={loading}
            mb="md"
          />
          <TextInput
            label="Email"
            placeholder="your@email.com"
            required
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={loading}
            mb="md"
          />
          <PasswordInput
            label="Password"
            placeholder="Your password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
            mb="md"
          />
          <Select
            label="Role"
            placeholder="Select role"
            data={[
              { value: 'viewer', label: 'Viewer' },
              { value: 'admin', label: 'Admin' },
            ]}
            value={role}
            onChange={(value: 'viewer' | 'admin') => setRole(value)}
            disabled={loading}
            mb="xl"
          />
          <Button fullWidth type="submit" loading={loading}>
            Create account
          </Button>
        </form>
      </Paper>
    </Container>
  );
}
