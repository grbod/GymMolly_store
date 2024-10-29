import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './OrderValidation.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function OrderValidation({ orderData, isSubmitting, onOrderSuccess }) {
  const navigate = useNavigate();
  const [existingPOs, setExistingPOs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch existing POs when component mounts
  useEffect(() => {
    fetchExistingPOs();
  }, []);

  const fetchExistingPOs = async () => {
    try {
      const response = await fetch(`${API_URL}/api/orders`);
      if (!response.ok) {
        throw new Error('Failed to fetch existing orders');
      }
      const orders = await response.json();
      const pos = orders.map(order => order.purchase_order_number.toLowerCase());
      setExistingPOs(pos);
      setIsLoading(false);
    } catch (error) {
      console.error('Error fetching POs:', error);
      setError('Failed to validate PO number');
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/');
  };

  const handleConfirm = async () => {
    document.body.classList.add('loading-cursor');
    
    // Check if PO already exists (case-insensitive)
    if (existingPOs.includes(orderData.po.toLowerCase())) {
      alert('This PO number has already been used. Please use a unique PO number.');
      document.body.classList.remove('loading-cursor');  // Remove cursor if validation fails
      return;
    }

    try {
      // Filter products to only include those with cases > 0 and format them correctly
      const productsToOrder = orderData.products
        .filter(product => product.cases > 0)
        .map(product => ({
          product_sku: product.sku,
          quantity: product.cases
        }));

      // Create the order data object
      const orderPayload = {
        purchase_order_number: orderData.po,
        shipping_address_id: orderData.address.id,
        shipping_method: orderData.shippingMethod,
        items: productsToOrder
      };

      const formData = new FormData();
      formData.append('data', JSON.stringify(orderPayload));
      
      if (orderData.attachment) {
        formData.append('attachment', orderData.attachment);
      }

      const response = await fetch(`${API_URL}/api/orders`, {
        method: 'POST',
        body: formData
      });

      const errorData = await response.text();

      if (!response.ok) {
        throw new Error(`Failed to submit order: ${response.status} ${response.statusText}. ${errorData}`);
      }

      // If successful
      alert('Order submitted successfully!');
      onOrderSuccess();
      navigate('/');
      
      // Move this line after all operations are complete
      setTimeout(() => {
        document.body.classList.remove('loading-cursor');
      }, 500);  // Add a small delay to ensure the cursor stays during navigation
      
    } catch (error) {
      console.error('Detailed error:', error);
      alert(`Failed to submit order: ${error.message}`);
      document.body.classList.remove('loading-cursor');  // Remove cursor if there's an error
    }
  };

  // Show loading state while fetching POs
  if (isLoading) {
    return (
      <div className="validation-container">
        <p>Validating order details...</p>
      </div>
    );
  }

  // Show error state if PO validation failed
  if (error) {
    return (
      <div className="validation-container">
        <p className="error-message">{error}</p>
        <button onClick={handleBack} className="cancel-button">
          Back to Order
        </button>
      </div>
    );
  }

  return (
    <div className="validation-container">
      <h2>Please Verify Your Order</h2>
      
      <section>
        <h3>Purchase Order</h3>
        <p>{orderData.po}</p>
        {existingPOs.includes(orderData.po.toLowerCase()) && (
          <p className="error-message">Warning: This PO number has already been used! Use a different PO#.</p>
        )}
      </section>

      <section>
        <h3>Shipping Address</h3>
        <p>{orderData.address.companyName}</p>
        <p>{orderData.address.addressLine1}</p>
        {orderData.address.addressLine2 && <p>{orderData.address.addressLine2}</p>}
        <p>{`${orderData.address.city}, ${orderData.address.state} ${orderData.address.zipCode}`}</p>
      </section>

      <section>
        <h3>Ordered Items</h3>
        <table>
          <thead>
            <tr>
              <th>Product</th>
              <th>Size</th>
              <th>Flavor</th>
              <th>Cases</th>
            </tr>
          </thead>
          <tbody>
            {orderData.products
              .filter(product => product.cases > 0)
              .map((product) => (
                <tr key={product.sku}>
                  <td>{product.product}</td>
                  <td>{product.size}</td>
                  <td>{product.flavor}</td>
                  <td>{product.cases}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </section>

      {orderData.attachment && (
        <section>
          <h3>Attachment</h3>
          <p>✓ File attached: {orderData.attachment.name}</p>
        </section>
      )}

      {/* Add new section for Shipping Method */}
      <section>
        <h3>Shipping Method</h3>
        <p>{orderData.shippingMethod}</p>
      </section>


      <div className="button-group">
        <button 
          onClick={handleBack} 
          className="cancel-button"
          disabled={isSubmitting}
        >
          Back to Order
        </button>
        <button 
          onClick={handleConfirm} 
          className="confirm-button"
          disabled={isSubmitting || existingPOs.includes(orderData.po.toLowerCase())}
        >
          {isSubmitting ? 'Submitting...' : 'Confirm Order'}
        </button>
      </div>
    </div>
  );
}

export default OrderValidation;
