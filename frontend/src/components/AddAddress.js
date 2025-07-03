import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './AddAddress.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

function AddAddress({ onAddressAdded }) {
  const [formData, setFormData] = useState({
    nickname: '',
    companyName: '',
    addressLine1: '',
    addressLine2: '',
    city: '',
    state: '',
    zipCode: '',
    phone: '',
    email: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [submittedAddress, setSubmittedAddress] = useState(null);

  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevState => ({
      ...prevState,
      [name]: value
    }));
  };

  // First step: Show confirmation
  const handleInitialSubmit = (e) => {
    e.preventDefault();
    setShowConfirmation(true);
  };

  // Second step: Actually submit to database
  const handleConfirmedSubmit = async () => {
    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_URL}/api/shipping-addresses`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorData?.message || 'Unknown error'}`);
      }

      const data = await response.json();
      console.log('Address successfully added:', data);
      setSubmittedAddress(data);
      
      // Add a small delay before navigation to ensure the server has time to process
      setTimeout(() => {
        navigate('/');
        // Trigger refresh of address list
        if (onAddressAdded) {
          onAddressAdded();
        }
      }, 2000);
    } catch (error) {
      console.error('Error adding address:', error);
      alert(`Failed to add address. Error: ${error.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Cancel confirmation
  const handleCancelConfirmation = () => {
    setShowConfirmation(false);
  };

  const handleGoBack = () => {
    navigate('/');
  };

  const states = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
  ];

  return (
    <div className="add-address-container">
      <h1>Gym Molly Add Address</h1>
      
      {!showConfirmation && !submittedAddress && (
        <form onSubmit={handleInitialSubmit}>
          <div className="form-group">
            <label htmlFor="nickname">Reference Nickname for Address Book</label>
            <input
              type="text"
              id="nickname"
              name="nickname"
              value={formData.nickname}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="companyName">Company Name *</label>
            <input
              type="text"
              id="companyName"
              name="companyName"
              value={formData.companyName}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group address-lines">
            <label htmlFor="addressLine1">Address *</label>
            <input
              type="text"
              id="addressLine1"
              name="addressLine1"
              placeholder="Address Line 1"
              value={formData.addressLine1}
              onChange={handleChange}
              required
            />
            <input
              type="text"
              id="addressLine2"
              name="addressLine2"
              placeholder="Address Line 2"
              value={formData.addressLine2}
              onChange={handleChange}
            />
          </div>
          <div className="form-group address-details">
            <input
              type="text"
              id="city"
              name="city"
              placeholder="City"
              value={formData.city}
              onChange={handleChange}
              required
              className="city"
            />
            <select
              id="state"
              name="state"
              value={formData.state}
              onChange={handleChange}
              required
              className="state"
            >
              <option value="">State</option>
              {states.map(state => (
                <option key={state} value={state}>{state}</option>
              ))}
            </select>
            <input
              type="text"
              id="zipCode"
              name="zipCode"
              placeholder="Zip Code"
              value={formData.zipCode}
              onChange={handleChange}
              required
              className="zip"
            />
          </div>
          <div className="form-group half-width-fields">
            <div className="half-width-field">
              <label htmlFor="phone">Phone *</label>
              <input
                type="tel"
                id="phone"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                required
              />
            </div>
            <div className="half-width-field">
              <label htmlFor="email">Email *</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
              />
            </div>
          </div>
          <div className="button-group">
            <button type="submit">Review Address</button>
            <button 
              type="button" 
              onClick={handleGoBack} 
              className="go-back-button"
            >
              Go Back
            </button>
          </div>
        </form>
      )}

      {showConfirmation && !submittedAddress && (
        <div className="confirmation-container">
          <h2>Please Confirm Address Details</h2>
          <div className="address-preview">
            <p><strong>Nickname:</strong> {formData.nickname}</p>
            <p><strong>Company:</strong> {formData.companyName}</p>
            <p><strong>Address:</strong> {formData.addressLine1}</p>
            {formData.addressLine2 && <p>{formData.addressLine2}</p>}
            <p>{formData.city}, {formData.state} {formData.zipCode}</p>
            <p><strong>Phone:</strong> {formData.phone}</p>
            <p><strong>Email:</strong> {formData.email}</p>
          </div>
          <div className="button-group">
            <button 
              onClick={handleConfirmedSubmit} 
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Submitting...' : 'Confirm & Submit'}
            </button>
            <button 
              onClick={handleCancelConfirmation}
              disabled={isSubmitting}
            >
              Edit Address
            </button>
          </div>
        </div>
      )}

      {submittedAddress && (
        <div className="success-message">
          <h2>Address Successfully Added!</h2>
          <p>Redirecting to main page...</p>
        </div>
      )}
    </div>
  );
}

export default AddAddress;
