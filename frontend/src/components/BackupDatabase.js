import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaArrowLeft, FaDatabase, FaCheck, FaExclamationTriangle, FaTimes } from 'react-icons/fa';
import { Alert, Spinner } from 'react-bootstrap';
import './BackupDatabase.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

function BackupDatabase() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [backing, setBacking] = useState(false);
  const [dbInfo, setDbInfo] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchDatabaseInfo();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchDatabaseInfo = async () => {
    try {
      const response = await fetch(`${API_URL}/api/database-info`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        if (response.status === 401) {
          navigate('/vieworders');
          return;
        }
        throw new Error('Failed to fetch database information');
      }

      const data = await response.json();
      setDbInfo(data);
      setLoading(false);
    } catch (err) {
      setError('Failed to load database information');
      setLoading(false);
    }
  };

  const handleBackupClick = async () => {
    await createBackup();
  };

  const createBackup = async () => {
    setBacking(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch(`${API_URL}/api/backup-database`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to create backup');
      }

      setSuccess(result.message);
      // Re-fetch database info in case size changed
      fetchDatabaseInfo();
    } catch (err) {
      setError(err.message);
    } finally {
      setBacking(false);
    }
  };

  if (loading) {
    return (
      <div className="backup-database-container">
        <div className="loading-spinner">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Loading...</span>
          </Spinner>
        </div>
      </div>
    );
  }

  const getSizeIcon = () => {
    if (!dbInfo) return null;
    
    if (!dbInfo.can_email) {
      return <FaTimes className="size-icon error" />;
    } else if (dbInfo.warning && dbInfo.estimated_zip_mb > 25) {
      return <FaExclamationTriangle className="size-icon warning" />;
    } else {
      return <FaCheck className="size-icon success" />;
    }
  };

  const getSizeClass = () => {
    if (!dbInfo) return '';
    
    if (!dbInfo.can_email) {
      return 'error';
    } else if (dbInfo.warning && dbInfo.estimated_zip_mb > 25) {
      return 'warning';
    } else {
      return 'success';
    }
  };

  return (
    <div className="backup-database-container">
      <div className="backup-header">
        <button 
          className="back-button"
          onClick={() => navigate('/inventory-settings')}
        >
          <FaArrowLeft /> Back to Inventory Settings
        </button>
        <h2>Database Backup Utility</h2>
      </div>

      {error && <Alert variant="danger" dismissible onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert variant="success" dismissible onClose={() => setSuccess('')}>{success}</Alert>}

      {dbInfo && (
        <div className="backup-content">
          <div className="database-info-card">
            <div className="info-header">
              <FaDatabase className="db-icon" />
              <h3>Database Information</h3>
            </div>
            
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">Database file:</span>
                <span className="info-value">{dbInfo.filename}</span>
              </div>
              
              <div className="info-item">
                <span className="info-label">Current size:</span>
                <span className="info-value">{dbInfo.size_readable}</span>
              </div>
              
              <div className="info-item">
                <span className="info-label">Estimated backup size:</span>
                <span className="info-value">~{dbInfo.estimated_zip_readable}</span>
              </div>
              
              <div className={`info-item status-item ${getSizeClass()}`}>
                <span className="info-label">SendGrid limit (30MB):</span>
                <span className="info-value">
                  {getSizeIcon()}
                  {dbInfo.warning || 'Within limit'}
                </span>
              </div>
            </div>

            <div className="backup-info">
              <p className="backup-destination">
                Backup will be sent to: <strong>greg@bodynutrition.com</strong>
              </p>
            </div>

            <div className="action-section">
              <button 
                className="backup-button"
                onClick={handleBackupClick}
                disabled={backing || !dbInfo.can_email}
              >
                {backing ? (
                  <>
                    <Spinner
                      as="span"
                      animation="border"
                      size="sm"
                      role="status"
                      aria-hidden="true"
                      className="me-2"
                    />
                    Creating backup...
                  </>
                ) : (
                  'Create and Email Backup'
                )}
              </button>
              
              {!dbInfo.can_email && (
                <p className="alternative-message">
                  Alternative: Download backup locally or use cloud storage
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default BackupDatabase;