import React, { useState, useEffect } from 'react';
import './ViewOrders.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function ViewOrders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
      setOrders(data);
    } catch (error) {
      console.error('Detailed error:', error);
      setError(error.message || 'Failed to load orders');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading orders...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="view-orders-container">
      <h2>Order History</h2>
      <table className="orders-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>PO Number</th>
            <th>Shipping Address</th>
            <th>Items Ordered</th>
            <th>Shipping Method</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((order) => (
            <tr key={order.order_id}>
              <td>{new Date(order.created_at).toLocaleDateString()}</td>
              <td>{order.purchase_order_number}</td>
              <td>
                {order.shipping_address.companyName}<br />
                {order.shipping_address.addressLine1}<br />
                {order.shipping_address.addressLine2 && <>{order.shipping_address.addressLine2}<br /></>}
                {`${order.shipping_address.city}, ${order.shipping_address.state} ${order.shipping_address.zipCode}`}
              </td>
              <td>
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
              </td>
              <td>{order.shipping_method || 'Not specified'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ViewOrders;
