import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactDataSheet from 'react-datasheet';
import { Modal, Button, Form, Alert, Spinner } from 'react-bootstrap';
import { FaArrowLeft, FaSave } from 'react-icons/fa';
import 'react-datasheet/lib/react-datasheet.css';
import './EditProducts.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

function EditProducts() {
  const navigate = useNavigate();
  const [originalData, setOriginalData] = useState([]);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [password, setPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');

  // Column headers
  const headers = [
    { value: 'SKU', readOnly: true },
    { value: 'Product Name', readOnly: true },
    { value: 'Size', readOnly: true },
    { value: 'Flavor', readOnly: true },
    { value: 'Units/Case', readOnly: true },
    { value: 'Length (in)', readOnly: true },
    { value: 'Width (in)', readOnly: true },
    { value: 'Height (in)', readOnly: true },
    { value: 'Weight (lbs)', readOnly: true }
  ];

  useEffect(() => {
    fetchProducts();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchProducts = async () => {
    try {
      const response = await fetch(`${API_URL}/api/products/full-details`, {
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
        throw new Error('Failed to fetch products');
      }

      const products = await response.json();
      
      // Convert products to datasheet format
      const sheetData = [headers];
      
      products.forEach(product => {
        sheetData.push([
          { value: product.sku, readOnly: true },
          { value: product.product },
          { value: product.size },
          { value: product.flavor },
          { value: product.unitsCs },
          { value: product.length.toString() },
          { value: product.width.toString() },
          { value: product.height.toString() },
          { value: product.weight.toString() }
        ]);
      });

      setData(sheetData);
      setOriginalData(JSON.parse(JSON.stringify(sheetData))); // Deep copy
      setLoading(false);
    } catch (err) {
      setError('Failed to load products');
      setLoading(false);
    }
  };

  const onCellsChanged = (changes) => {
    const grid = [...data];
    changes.forEach(({ cell, row, col, value }) => {
      grid[row][col] = { ...grid[row][col], value };
    });
    setData(grid);
  };

  const hasChanges = () => {
    if (data.length !== originalData.length) return true;
    
    for (let i = 1; i < data.length; i++) { // Skip header row
      for (let j = 0; j < data[i].length; j++) {
        if (data[i][j].value !== originalData[i][j].value) {
          return true;
        }
      }
    }
    return false;
  };

  const handleSubmit = () => {
    if (!hasChanges()) {
      setError('No changes to save');
      return;
    }

    // Validate numeric fields
    for (let i = 1; i < data.length; i++) {
      const length = parseFloat(data[i][5].value);
      const width = parseFloat(data[i][6].value);
      const height = parseFloat(data[i][7].value);
      const weight = parseFloat(data[i][8].value);

      if (isNaN(length) || isNaN(width) || isNaN(height) || isNaN(weight)) {
        setError(`Invalid numeric values in row ${i}. Length, width, height, and weight must be numbers.`);
        return;
      }
    }

    setShowPasswordModal(true);
  };

  const handlePasswordSubmit = async () => {
    setPasswordError('');
    
    if (!password) {
      setPasswordError('Password is required');
      return;
    }

    setSaving(true);

    // Prepare data for submission
    const products = [];
    for (let i = 1; i < data.length; i++) { // Skip header row
      products.push({
        sku: data[i][0].value,
        product: data[i][1].value,
        size: data[i][2].value,
        flavor: data[i][3].value,
        unitsCs: data[i][4].value,
        length: parseFloat(data[i][5].value),
        width: parseFloat(data[i][6].value),
        height: parseFloat(data[i][7].value),
        weight: parseFloat(data[i][8].value)
      });
    }

    try {
      const response = await fetch(`${API_URL}/api/products/bulk-update`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          password: password,
          products: products
        })
      });

      const result = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          setPasswordError(result.error || 'Invalid password');
          setSaving(false);
          return;
        }
        throw new Error(result.error || 'Failed to update products');
      }

      setSuccess(result.message);
      setOriginalData(JSON.parse(JSON.stringify(data))); // Update original data
      setShowPasswordModal(false);
      setPassword('');
      setSaving(false);

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.message);
      setSaving(false);
      setShowPasswordModal(false);
      setPassword('');
    }
  };

  const handleRevert = () => {
    setData(JSON.parse(JSON.stringify(originalData)));
    setError('');
    setSuccess('Changes reverted');
    setTimeout(() => setSuccess(''), 2000);
  };

  if (loading) {
    return (
      <div className="edit-products-container">
        <div className="loading-spinner">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Loading...</span>
          </Spinner>
        </div>
      </div>
    );
  }

  return (
    <div className="edit-products-container">
      <div className="edit-products-header">
        <button 
          className="back-button"
          onClick={() => navigate('/inventory-settings')}
        >
          <FaArrowLeft /> Back to Inventory Settings
        </button>
        <h2>Edit Product Details</h2>
      </div>

      {error && <Alert variant="danger" dismissible onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert variant="success" dismissible onClose={() => setSuccess('')}>{success}</Alert>}

      <div className="spreadsheet-info">
        <p>Click on any cell (except SKU) to edit. Press Enter or Tab to save changes to the cell.</p>
      </div>

      <div className="spreadsheet-container">
        <ReactDataSheet
          data={data}
          valueRenderer={(cell) => cell.value}
          onCellsChanged={onCellsChanged}
          className="custom-spreadsheet"
        />
      </div>

      <div className="action-buttons">
        <Button 
          variant="secondary" 
          onClick={handleRevert}
          disabled={!hasChanges()}
        >
          Revert Changes
        </Button>
        <Button 
          variant="primary" 
          onClick={handleSubmit}
          disabled={!hasChanges()}
        >
          <FaSave /> Save Changes
        </Button>
      </div>

      {/* Password Confirmation Modal */}
      <Modal show={showPasswordModal} onHide={() => !saving && setShowPasswordModal(false)}>
        <Modal.Header closeButton={!saving}>
          <Modal.Title>Confirm Changes</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group>
            <Form.Label>Enter password to confirm bulk update:</Form.Label>
            <Form.Control
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              disabled={saving}
              isInvalid={!!passwordError}
            />
            <Form.Control.Feedback type="invalid">
              {passwordError}
            </Form.Control.Feedback>
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button 
            variant="secondary" 
            onClick={() => {
              setShowPasswordModal(false);
              setPassword('');
              setPasswordError('');
            }}
            disabled={saving}
          >
            Cancel
          </Button>
          <Button 
            variant="primary" 
            onClick={handlePasswordSubmit}
            disabled={saving}
          >
            {saving ? (
              <>
                <Spinner
                  as="span"
                  animation="border"
                  size="sm"
                  role="status"
                  aria-hidden="true"
                  className="me-2"
                />
                Saving...
              </>
            ) : (
              'Confirm Update'
            )}
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}

export default EditProducts;