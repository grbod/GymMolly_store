import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaArrowLeft, FaTrash } from 'react-icons/fa';
import './DeleteOrders.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

function DeleteOrders({ onOrderDeleted }) {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await fetch(`${API_URL}/api/orders`, {
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch orders');
      }

      const data = await response.json();
      // Sort by date, newest first
      const sortedOrders = data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      setOrders(sortedOrders);
    } catch (err) {
      setError('Failed to load orders');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteOrder = async (orderId, poNumber) => {
    // First password prompt
    const password = prompt("Please enter the admin password to DELETE this order:");
    
    // Check if password is correct (GREGS)
    if (password !== 'GREGS') {
      if (password !== null) { // User didn't cancel
        alert('Incorrect password. Order will not be deleted.');
      }
      return;
    }
    
    // If password is correct, show serious confirmation dialog
    if (!window.confirm(`⚠️ WARNING: This will PERMANENTLY DELETE order ${poNumber}!\n\nThis action cannot be undone.\n\nAre you absolutely sure you want to delete this order?`)) {
      return;
    }
    
    try {
      const response = await fetch(`${API_URL}/api/orders/${orderId}/delete`, {
        method: 'DELETE',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to delete order');
      }
      
      // Remove order from state
      setOrders(orders.filter(o => o.order_id !== orderId));
      
      // Call parent callback if provided
      if (onOrderDeleted) {
        onOrderDeleted();
      }
      
      // Show success message
      alert(`Order ${poNumber} has been permanently deleted.`);
      
    } catch (error) {
      console.error('Error deleting order:', error);
      alert(`Failed to delete order: ${error.message}`);
    }
  };

  // Filter orders based on search and status
  const filteredOrders = orders.filter(order => {
    const matchesSearch = order.purchase_order_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         order.shipping_address.companyName.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === 'all' || order.order_status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  if (loading) return <div className="loading">Loading orders...</div>;

  return (
    <div className="delete-orders-container">
      <div className="delete-orders-header">
        <button 
          className="back-button"
          onClick={() => navigate('/inventory-settings')}
        >
          <FaArrowLeft /> Back to Settings
        </button>
        <h2>Delete Test Orders</h2>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="warning-banner">
        <strong>⚠️ Warning:</strong> This feature is for removing test orders only. 
        Deleted orders cannot be recovered. Only Processing and Voided orders can be deleted.
      </div>

      <div className="filters-section">
        <div className="search-box">
          <input
            type="text"
            className="form-control search-input"
            placeholder="Search by PO number or company name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <div className="status-filter">
          <label htmlFor="status-select">Filter by status:</label>
          <select
            id="status-select"
            className="form-select"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="all">All Orders</option>
            <option value="Processing">Processing</option>
            <option value="Voided">Voided</option>
            <option value="Shipped">Shipped</option>
          </select>
        </div>
      </div>

      <div className="orders-list">
        {filteredOrders.length === 0 ? (
          <div className="no-orders">
            {searchTerm || filterStatus !== 'all' 
              ? 'No orders match your search criteria.' 
              : 'No orders available.'}
          </div>
        ) : (
          filteredOrders.map(order => {
            const canDelete = order.order_status === 'Processing' || order.order_status === 'Voided';
            const totalItems = order.items.reduce((sum, item) => sum + item.quantity, 0);
            
            return (
              <div key={order.order_id} className="order-card">
                <div className="order-header">
                  <div className="order-main-info">
                    <h4>PO# {order.purchase_order_number}</h4>
                    <span className={`status-badge status-${order.order_status.toLowerCase()}`}>
                      {order.order_status}
                    </span>
                  </div>
                </div>
                
                <div className="order-details">
                  <p className="company-name">{order.shipping_address.companyName}</p>
                  <p className="order-summary">
                    {order.items.length} product{order.items.length !== 1 ? 's' : ''}, {totalItems} case{totalItems !== 1 ? 's' : ''}
                  </p>
                </div>
                
                <div className="order-date">
                  {new Date(order.created_at).toLocaleDateString()}
                </div>
                
                <div className="order-actions">
                  {canDelete ? (
                    <button
                      className="delete-order-button"
                      onClick={() => handleDeleteOrder(order.order_id, order.purchase_order_number)}
                    >
                      <FaTrash /> Delete
                    </button>
                  ) : (
                    <span className="cannot-delete-message">
                      {order.order_status === 'Shipped' ? 'Shipped' : 'Locked'}
                    </span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

export default DeleteOrders;