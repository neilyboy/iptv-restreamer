import React from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import { format } from 'date-fns';

function StreamLogs({ logs }) {
  if (!logs || logs.length === 0) {
    return (
      <Paper elevation={1} sx={{ p: 2, mt: 2 }}>
        <Typography variant="body2" color="text.secondary">
          No logs available
        </Typography>
      </Paper>
    );
  }

  const getLogClass = (logType) => {
    switch (logType) {
      case 'info':
        return 'log-info';
      case 'error':
        return 'log-error';
      case 'warning':
        return 'log-warning';
      default:
        return '';
    }
  };

  return (
    <Paper elevation={1} sx={{ mt: 2 }}>
      <Box sx={{ p: 2, pb: 0 }}>
        <Typography variant="h6" gutterBottom>
          Stream Logs
        </Typography>
      </Box>
      <List className="stream-logs" dense>
        {logs.map((log) => (
          <React.Fragment key={log.id}>
            <ListItem className={`log-entry ${getLogClass(log.log_type)}`}>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" component="span" sx={{ fontWeight: 'bold' }}>
                      {log.log_type.toUpperCase()}
                    </Typography>
                    <Typography variant="body2" component="span" color="text.secondary">
                      {format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss')}
                    </Typography>
                  </Box>
                }
                secondary={log.message}
                secondaryTypographyProps={{ 
                  component: 'div',
                  style: { 
                    whiteSpace: 'pre-wrap', 
                    wordBreak: 'break-word' 
                  } 
                }}
              />
            </ListItem>
            <Divider component="li" />
          </React.Fragment>
        ))}
      </List>
    </Paper>
  );
}

export default StreamLogs;
