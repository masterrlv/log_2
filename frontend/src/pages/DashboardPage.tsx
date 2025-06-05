import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Title,
  Paper,
  Text,
  Button,
  Group,
  TextInput,
  Select,
  Table,
  LoadingOverlay,
  Tabs,
  FileButton,
  Progress,
  Alert,
  Space,
  Textarea,
  Box,
} from '@mantine/core';
import { IconUpload, IconSearch, IconAlertCircle, IconFileUpload } from '@tabler/icons-react';
import { uploads, logs } from '../services/api';

export function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [logLevel, setLogLevel] = useState<string | null>(null);
  const [source, setSource] = useState<string | null>(null);
  const [logResults, setLogResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const handleFileUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setUploadStatus('Uploading file...');
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await uploads.uploadLog(file);
      
      // Simulate progress (in a real app, you'd use axios's onUploadProgress)
      for (let i = 0; i <= 100; i += 10) {
        setTimeout(() => {
          setUploadProgress(i);
          if (i === 100) {
            setUploadStatus('File uploaded successfully! Processing logs...');
            
            // Poll for processing status
            const uploadId = response.data.id;
            const checkStatus = async () => {
              try {
                const statusResponse = await uploads.getUploadStatus(uploadId);
                if (statusResponse.data.status === 'completed') {
                  setUploadStatus('Logs processed successfully!');
                  setIsUploading(false);
                } else if (statusResponse.data.status === 'failed') {
                  setUploadStatus('Failed to process logs.');
                  setIsUploading(false);
                } else {
                  setTimeout(checkStatus, 2000); // Check again in 2 seconds
                }
              } catch (err) {
                setUploadStatus('Error checking upload status.');
                setIsUploading(false);
              }
            };
            
            checkStatus();
          }
        }, i * 50);
      }
    } catch (err: any) {
      setUploadStatus(`Error: ${err.response?.data?.detail || 'Upload failed'}`);
      setIsUploading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim() && !logLevel && !source) {
      setSearchError('Please enter a search term or select a filter');
      return;
    }

    setIsSearching(true);
    setSearchError(null);

    try {
      const response = await logs.search({
        q: searchQuery.trim() || undefined,
        log_level: logLevel || undefined,
        source: source || undefined,
        page: 1,
        per_page: 50,
      });
      
      setLogResults(response.data.logs || []);
    } catch (err: any) {
      setSearchError(err.response?.data?.detail || 'Search failed');
    } finally {
      setIsSearching(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Redirect to login if not authenticated
  useEffect(() => {
    // if (!user) {
    //   navigate('/login');
    // }
  }, [user, navigate]);

  return (
    <Container size="lg" py="xl">
      <Group position="apart" mb="xl">
        <Title>Log Management Dashboard</Title>
        <Button variant="outline" onClick={handleLogout}>
          Logout
        </Button>
      </Group>

      <Tabs defaultValue="upload">
        <Tabs.List>
          <Tabs.Tab value="upload" icon={<IconUpload size={14} />}>Upload Logs</Tabs.Tab>
          <Tabs.Tab value="search" icon={<IconSearch size={14} />}>Search Logs</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="upload" pt="xl">
          <Paper shadow="sm" p="md" withBorder>
            <Title order={3} mb="md">Upload Log File</Title>
            
            {uploadStatus && (
              <Alert 
                color={uploadStatus.includes('Error') ? 'red' : 'blue'} 
                icon={<IconAlertCircle size={16} />}
                mb="md"
              >
                {uploadStatus}
              </Alert>
            )}
            
            <Group position="center" mb="md">
              <FileButton onChange={setFile} accept="text/plain,application/log,.log">
                {(props) => (
                  <Button leftIcon={<IconFileUpload size={16} />} {...props}>
                    {file ? file.name : 'Select log file'}
                  </Button>
                )}
              </FileButton>
              
              <Button 
                onClick={handleFileUpload} 
                disabled={!file || isUploading}
                loading={isUploading}
              >
                Upload & Process
              </Button>
            </Group>
            
            {uploadProgress > 0 && uploadProgress < 100 && (
              <Progress value={uploadProgress} animate striped size="sm" />
            )}
          </Paper>
        </Tabs.Panel>

        <Tabs.Panel value="search" pt="xl">
          <Paper shadow="sm" p="md" withBorder>
            <Title order={3} mb="md">Search Logs</Title>
            
            <Group spacing="md" mb="md">
              <TextInput
                placeholder="Search logs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{ flex: 1 }}
              />
              
              <Select
                placeholder="Log level"
                data={['ERROR', 'WARNING', 'INFO', 'DEBUG']}
                value={logLevel}
                onChange={setLogLevel}
                clearable
              />
              
              <Select
                placeholder="Source"
                data={['Apache', 'Nginx', 'System', 'Application']}
                value={source}
                onChange={setSource}
                clearable
              />
              
              <Button 
                onClick={handleSearch}
                loading={isSearching}
                leftIcon={<IconSearch size={16} />}
              >
                Search
              </Button>
            </Group>
            
            {searchError && (
              <Alert color="red" mb="md" icon={<IconAlertCircle size={16} />}>
                {searchError}
              </Alert>
            )}
            
            <div style={{ position: 'relative' }}>
              <LoadingOverlay visible={isSearching} overlayBlur={2} />
              
              {logResults.length > 0 ? (
                <Table striped>
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th>Level</th>
                      <th>Source</th>
                      <th>Message</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logResults.map((log, index) => (
                      <tr key={index}>
                        <td>{new Date(log.timestamp).toLocaleString()}</td>
                        <td>{log.log_level}</td>
                        <td>{log.source}</td>
                        <td>
                          <Text lineClamp={2} style={{ maxWidth: 400 }}>
                            {log.message}
                          </Text>
                          {log.additional_fields && (
                            <Text size="xs" color="dimmed">
                              {JSON.stringify(log.additional_fields)}
                            </Text>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              ) : (
                !isSearching && (
                  <Text color="dimmed" align="center" py="xl">
                    No logs found. Try adjusting your search criteria.
                  </Text>
                )
              )}
            </div>
          </Paper>
        </Tabs.Panel>
      </Tabs>
    </Container>
  );
}
