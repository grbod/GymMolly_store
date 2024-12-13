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
      document.body.classList.remove('loading-cursor');
      return;
    }

    // Check if attachment exists
    if (!orderData.attachment || orderData.attachment.length === 0) {
      alert('Please attach shipping label(s) before submitting the order.');
      document.body.classList.remove('loading-cursor');
      return;
    }

    // Check if number of attachments matches number of cases
    const totalCases = orderData.products.reduce((sum, product) => sum + (parseInt(product.cases) || 0), 0);
    if (orderData.attachment.length !== totalCases) {
      alert('The number of attached shipping labels must match the total number of cases ordered.');
      document.body.classList.remove('loading-cursor');
      return;
    }

    try {
      // First process the shipping labels
      const labelFormData = new FormData();
      orderData.attachment.forEach(file => {
        labelFormData.append('files', file);
      });

      const labelResponse = await fetch(`${API_URL}/api/process-labels`, {
        method: 'POST',
        body: labelFormData,
        credentials: 'include'
      });

      if (!labelResponse.ok) {
        const errorData = await labelResponse.json();
        throw new Error(errorData.error || 'Failed to process shipping labels');
      }

      const { processedFiles } = await labelResponse.json();

      // Create the order data object with processed labels
      const productsToOrder = orderData.products
        .filter(product => product.cases > 0)
        .map(product => ({
          product_sku: product.sku,
          quantity: product.cases
        }));

      const orderPayload = {
        purchase_order_number: orderData.po,
        shipping_address_id: orderData.address.id,
        shipping_method: orderData.shippingMethod,
        items: productsToOrder
      };

      // Submit the order with processed labels
      const formData = new FormData();
      formData.append('data', JSON.stringify(orderPayload));
      
      // Append the original files directly instead of the processed ones
      orderData.attachment.forEach((file, index) => {
        formData.append('attachment', file);
      });

      const response = await fetch(`${API_URL}/api/orders`, {
        method: 'POST',
        credentials: 'include',
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
        <h3><strong>Purchase Order</strong></h3>
        <p>{orderData.po}</p>
        {existingPOs.includes(orderData.po.toLowerCase()) && (
          <p className="error-message">Warning: This PO number has already been used! Use a different PO#.</p>
        )}
      </section>

      <section>
        <h3><strong>Shipping Address</strong></h3>
        <p>{orderData.address.companyName}</p>
        <p>{orderData.address.addressLine1}</p>
        {orderData.address.addressLine2 && <p>{orderData.address.addressLine2}</p>}
        <p>{`${orderData.address.city}, ${orderData.address.state} ${orderData.address.zipCode}`}</p>
      </section>

      <section>
        <h3><strong>Ordered Items</strong></h3>
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

      {orderData.attachment && orderData.attachment.length > 0 && (
        <section>
          <h3><strong>Attachments</strong></h3>
          {orderData.attachment.map((file, index) => (
            <p key={index}>✓ File attached: {file.name}</p>
          ))}
        </section>
      )}

      <section>
        <h3><strong>Shipping Method</strong></h3>
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
