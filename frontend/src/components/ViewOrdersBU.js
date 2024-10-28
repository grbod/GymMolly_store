import React, { useState, useEffect } from 'react';
import './ViewOrders.css';

function ViewOrders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/orders');
      if (!response.ok) {
        throw new Error('Failed to fetch orders');
      }
      const data = await response.json();
      setOrders(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching orders:', error);
      setError('Failed to load orders');
      setLoading(false);
    }
  };

  if (loading) return <div>Loading orders...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="page-wrapper">
      <div className="view-orders-container">
        <h2>Order History</h2>
        <table className="orders-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>PO Number</th>
              <th>Shipping Address</th>
              <th>Items Ordered</th>
              <th>Attachment</th>
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
                <td>
                  {order.has_attachment ? (
                    <a 
                      href={`http://localhost:5000/api/orders/${order.order_id}/attachment`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      View Attachment
                    </a>
                  ) : (
                    'No attachment'
                  )}
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
