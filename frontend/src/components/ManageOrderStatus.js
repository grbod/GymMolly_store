import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactDataSheet from 'react-datasheet';
import { Modal, Button, Form, Alert, Spinner } from 'react-bootstrap';
import { FaArrowLeft, FaTruck, FaBan } from 'react-icons/fa';
import 'react-datasheet/lib/react-datasheet.css';
import './ManageOrderStatus.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

function ManageOrderStatus({ onInventoryUpdate }) {
  const navigate = useNavigate();
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [password, setPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [pendingAction, setPendingAction] = useState(null);

  // Column headers
  const headers = [
    { value: 'Order ID', readOnly: true },
    { value: 'PO Number', readOnly: true },
    { value: 'Date', readOnly: true },
    { value: 'Total Items', readOnly: true },
    { value: 'Status', readOnly: true },
    { value: 'Actions', readOnly: true }
  ];

  useEffect(() => {
    fetchOrders();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchOrders = async () => {
    try {
      const response = await fetch(`${API_URL}/api/orders`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch orders');
      }

      const orders = await response.json();
      
      // Filter only Processing orders and convert to datasheet format
      const sheetData = [headers];
      
      orders
        .filter(order => order.order_status === 'Processing')
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at)) // Sort by most recent first
        .forEach(order => {
          const totalItems = order.items.reduce((sum, item) => sum + item.quantity, 0);
          const orderDate = new Date(order.created_at).toLocaleDateString();
          
          sheetData.push([
            { value: order.order_id.toString(), readOnly: true },
            { value: order.purchase_order_number, readOnly: true },
            { value: orderDate, readOnly: true },
            { value: totalItems.toString(), readOnly: true },
            { 
              value: 'Processing', 
              readOnly: true,
              className: 'status-processing'
            },
            { 
              value: 'actions', 
              readOnly: true,
              component: (
                <div className="action-buttons-cell">
                  <button 
                    className="btn-action btn-ship"
                    onClick={() => handleStatusChange(order.order_id, 'Shipped')}
                    title="Mark as Shipped"
                  >
                    <FaTruck /> Ship
                  </button>
                  <button 
                    className="btn-action btn-cancel"
                    onClick={() => handleStatusChange(order.order_id, 'Manually Cancelled')}
                    title="Cancel Order"
                  >
                    <FaBan /> Cancel
                  </button>
                </div>
              ),
              forceComponent: true
            }
          ]);
        });

      setData(sheetData);
      setLoading(false);
    } catch (err) {
      setError('Failed to load orders');
      setLoading(false);
    }
  };

  const handleStatusChange = (orderId, newStatus) => {
    setPendingAction({ orderId, newStatus });
    setShowPasswordModal(true);
  };

  const handlePasswordSubmit = async () => {
    setPasswordError('');
    
    if (!password) {
      setPasswordError('Password is required');
      return;
    }

    if (!pendingAction) {
      return;
    }

    setUpdating(true);

    try {
      const response = await fetch(`${API_URL}/api/orders/${pendingAction.orderId}/update-status`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          status: pendingAction.newStatus,
          password: password
        })
      });

      const result = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          setPasswordError(result.error || 'Invalid password');
          setUpdating(false);
          return;
        }
        throw new Error(result.error || 'Failed to update order status');
      }

      setSuccess(result.message);
      setShowPasswordModal(false);
      setPassword('');
      setPendingAction(null);
      setUpdating(false);

      // Refresh the orders list
      await fetchOrders();
      
      // Refresh inventory if the order was cancelled (which affects inventory)
      if (pendingAction.newStatus === 'Manually Cancelled' && onInventoryUpdate) {
        onInventoryUpdate();
      }

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.message);
      setUpdating(false);
      setShowPasswordModal(false);
      setPassword('');
      setPendingAction(null);
    }
  };

  const closePasswordModal = () => {
    if (!updating) {
      setShowPasswordModal(false);
      setPassword('');
      setPasswordError('');
      setPendingAction(null);
    }
  };

  if (loading) {
    return (
      <div className="manage-order-status-container">
        <div className="loading-spinner">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Loading...</span>
          </Spinner>
        </div>
      </div>
    );
  }

  return (
    <div className="manage-order-status-container">
      <div className="manage-order-status-header">
        <button 
          className="back-button"
          onClick={() => navigate('/inventory-settings')}
        >
          <FaArrowLeft /> Back to Inventory Settings
        </button>
        <h2>Manage Order Status</h2>
      </div>

      {error && <Alert variant="danger" dismissible onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert variant="success" dismissible onClose={() => setSuccess('')}>{success}</Alert>}

      <div className="spreadsheet-info">
        <p>View and update order status for processing orders. Use the action buttons to mark orders as shipped or cancelled.</p>
      </div>

      {data.length > 1 ? (
        <div className="spreadsheet-container">
          <ReactDataSheet
            data={data}
            valueRenderer={(cell) => cell.value}
            onCellsChanged={() => {}} // Read-only, no changes allowed
            className="custom-spreadsheet order-status-spreadsheet"
          />
        </div>
      ) : (
        <div className="no-orders-message">
          <p>No processing orders found.</p>
        </div>
      )}

      {/* Password Confirmation Modal */}
      <Modal show={showPasswordModal} onHide={closePasswordModal}>
        <Modal.Header closeButton={!updating}>
          <Modal.Title>
            {pendingAction?.newStatus === 'Shipped' ? 'Mark Order as Shipped' : 'Cancel Order'}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {pendingAction?.newStatus === 'Manually Cancelled' && (
            <Alert variant="warning">
              <strong>Warning:</strong> Cancelling this order will replenish the inventory for all items in the order.
            </Alert>
          )}
          <Form.Group>
            <Form.Label>Enter password to confirm:</Form.Label>
            <Form.Control
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              disabled={updating}
              isInvalid={!!passwordError}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !updating) {
                  handlePasswordSubmit();
                }
              }}
              autoFocus
            />
            <Form.Control.Feedback type="invalid">
              {passwordError}
            </Form.Control.Feedback>
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button 
            variant="secondary" 
            onClick={closePasswordModal}
            disabled={updating}
          >
            Cancel
          </Button>
          <Button 
            variant={pendingAction?.newStatus === 'Manually Cancelled' ? 'danger' : 'primary'}
            onClick={handlePasswordSubmit}
            disabled={updating}
          >
            {updating ? (
              <>
                <Spinner
                  as="span"
                  animation="border"
                  size="sm"
                  role="status"
                  aria-hidden="true"
                  className="me-2"
                />
                Updating...
              </>
            ) : (
              pendingAction?.newStatus === 'Shipped' ? 'Mark as Shipped' : 'Cancel Order'
            )}
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}

export default ManageOrderStatus;