import React, { useState, useEffect } from 'react';
import './ViewOrders.css';
import { useNavigate } from 'react-router-dom';
import { FaArrowLeft, FaFileExport, FaCalculator } from 'react-icons/fa';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function ViewOrders({ onInventoryUpdate }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await fetch(`${API_URL}/api/orders`);
      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`Failed to fetch orders: ${response.status} ${response.statusText}. ${errorData}`);
      }
      const data = await response.json();
      const sortedOrders = data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      setOrders(sortedOrders);
    } catch (error) {
      console.error('Detailed error:', error);
      setError(error.message || 'Failed to load orders');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadAttachment = async (orderId, poNumber) => {
    try {
      const response = await fetch(`${API_URL}/api/orders/${orderId}/attachment`);
      
      if (!response.ok) {
        throw new Error('Failed to download attachment');
      }

      // Create blob from response
      const blob = await response.blob();
      
      // Create download link with PO number in filename
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `PO_${poNumber}_shipping_labels.pdf`;
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading attachment:', error);
      alert('Failed to download attachment');
    }
  };

  const handleVoidOrder = async (orderId) => {
    // Prompt for password
    const password = prompt("Please enter the admin password to void this order:");
    
    // Check if password is correct (GREGS)
    if (password !== 'GREGS') {
      alert('Incorrect password. Order will not be voided.');
      return;
    }
    
    // If password is correct, show confirmation dialog
    if (!window.confirm('Are you sure you want to void this order?')) {
      return;
    }
    
    try {
      const response = await fetch(`${API_URL}/api/orders/${orderId}/void`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to void order');
      }
      
      // Refresh orders list
      fetchOrders();
      
      // Update inventory in real-time
      onInventoryUpdate();
      
    } catch (error) {
      console.error('Error voiding order:', error);
      alert(error.message);
    }
  };

  const handleBillingExport = async () => {
    try {
      // Create simplified CSV content for billing
      const headers = [
        'Order_Number',
        'Store_Name',
        'Total_Cases',
        'Order_Status',
        'Shipping_Method'
      ];

      // Group by order and sum total cases
      const billingRows = orders.map(order => {
        const totalCases = order.items.reduce((sum, item) => sum + item.quantity, 0);
        return [
          order.purchase_order_number,
          order.shipping_address.companyName,
          totalCases,
          order.order_status || 'Processing',
          order.shipping_method || 'Not specified'
        ];
      });

      // Convert to CSV
      const csvContent = [
        headers.join(','),
        ...billingRows.map(row => row.map(cell => 
          `"${(cell || '').toString().replace(/"/g, '""')}"`
        ).join(','))
      ].join('\n');

      // Create and download file
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // Generate filename with current date
      const date = new Date().toISOString().split('T')[0].replace(/-/g, '_');
      link.download = `billing_export_${date}.csv`;
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (error) {
      console.error('Error exporting billing data:', error);
      alert('Failed to export billing data');
    }
  };

  const handleExport = async () => {
    try {
      // Create CSV content
      const headers = [
        'Order_Date',
        'Order_Number',
        'Store_Number',
        'Store_Name',
        'Store_Address',
        'Store_City',
        'Store_State',
        'Store_Zip',
        'Shipping_Method',
        'Product_Name',
        'Product_Size',
        'Product_Flavor',
        'Product_Cases',
        'Order_Status'
      ];

      const rows = orders.flatMap(order => 
        order.items.map(item => [
          new Date(order.created_at).toLocaleDateString(),
          order.purchase_order_number,
          order.shipping_address.companyName.split(' ')[0],
          order.shipping_address.companyName,
          order.shipping_address.addressLine1,
          order.shipping_address.city,
          order.shipping_address.state,
          order.shipping_address.zipCode,
          order.shipping_method,
          item.product,
          item.size,
          item.flavor,
          item.quantity,
          order.order_status || 'Processing'
        ])
      );

      // Convert to CSV
      const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => 
          `"${(cell || '').toString().replace(/"/g, '""')}"`
        ).join(','))
      ].join('\n');

      // Create and download file
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // Generate filename with current date
      const date = new Date().toISOString().split('T')[0].replace(/-/g, '_');
      link.download = `orders_export_${date}.csv`;
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (error) {
      console.error('Error exporting orders:', error);
      alert('Failed to export orders');
    }
  };

  if (loading) return <div>Loading orders...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="view-orders-container">
      <div className="orders-header">
        <div className="header-content">
          <h2>Order History</h2>
          <div className="header-buttons">
            <button 
              className="action-button back-button"
              onClick={() => navigate('/')}
            >
              <FaArrowLeft className="button-icon" /> Back to Order Form
            </button>
            
            <button 
              className="action-button export-button"
              onClick={handleExport}
            >
              <FaFileExport className="button-icon" /> Export to CSV
            </button>
            
            <button 
              className="action-button billing-export-button"
              onClick={handleBillingExport}
            >
              <FaCalculator className="button-icon" /> Export for Billing
            </button>
          </div>
        </div>
      </div>
      <div className="orders-table-container">
        <table className="orders-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>PO Number</th>
              <th>Shipping Address</th>
              <th>Items Ordered</th>
              <th>Shipping Method</th>
              <th>Attachments</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {orders
              .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
              .map((order) => (
                <tr key={order.order_id} className="order-row">
                  <td>{new Date(order.created_at).toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: '2-digit' })}</td>
                  <td className="po-number">{order.purchase_order_number}</td>
                  <td className="address-cell">
                    <div className="address-content">
                      <strong>{order.shipping_address.companyName}</strong>
                      <span>{order.shipping_address.addressLine1}</span>
                      {order.shipping_address.addressLine2 && (
                        <span>{order.shipping_address.addressLine2}</span>
                      )}
                      <span>
                        {`${order.shipping_address.city}, ${order.shipping_address.state} ${order.shipping_address.zipCode}`}
                      </span>
                    </div>
                  </td>
                  <td>
                    <div className="items-table-container">
                      <table className="items-table">
                        <thead>
                          <tr>
                            <th>Product</th>
                            <th>Size</th>
                            <th>Flavor</th>
                            <th>Cases</th>
                          </tr>
                        </thead>
                        <tbody>
                          {order.items.map((item) => (
                            <tr key={`${order.order_id}-${item.sku}`}>
                              <td>{item.product}</td>
                              <td>{item.size}</td>
                              <td>{item.flavor}</td>
                              <td>{item.quantity}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </td>
                  <td className="shipping-method">{order.shipping_method || 'Not specified'}</td>
                  <td>
                    {order.has_attachment ? (
                      <button
                        onClick={() => handleDownloadAttachment(order.order_id, order.purchase_order_number)}
                        className="action-button download-button"
                      >
                        Download Labels
                      </button>
                    ) : (
                      <span className="no-attachment">No attachments</span>
                    )}
                  </td>
                  <td>
                    <span className={`status-badge status-${(order.order_status || 'Processing').toLowerCase()}`}>
                      {order.order_status || 'Processing'}
                    </span>
                  </td>
                  <td>
                    <button
                      className="action-button void-button"
                      onClick={() => handleVoidOrder(order.order_id)}
                      disabled={order.order_status !== 'Processing'}
                    >
                      Void Order
                    </button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default ViewOrders;
