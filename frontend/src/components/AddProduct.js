import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaArrowLeft } from 'react-icons/fa';
import './AddProduct.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

function AddProduct({ onProductAdded }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  
  const [formData, setFormData] = useState({
    sku: '',
    product: '',
    size: '',
    flavor: '',
    unitsCs: '',
    quantity: 0,
    length: '',
    width: '',
    height: '',
    weight: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess(false);

    // Validate required fields
    if (!formData.sku || !formData.product || !formData.size || !formData.flavor || !formData.unitsCs) {
      setError('Please fill in all required product fields');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/products`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to add product');
      }

      setSuccess(true);
      setFormData({
        sku: '',
        product: '',
        size: '',
        flavor: '',
        unitsCs: '',
        quantity: 0,
        length: '',
        width: '',
        height: '',
        weight: ''
      });

      // Call parent callback if provided
      if (onProductAdded) {
        onProductAdded();
      }

      // Navigate back after a short delay
      setTimeout(() => {
        navigate('/inventory-settings');
      }, 2000);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="add-product-container">
      <div className="add-product-header">
        <button 
          className="back-button"
          onClick={() => navigate('/inventory-settings')}
        >
          <FaArrowLeft /> Back to Settings
        </button>
        <h2>Add New Product</h2>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {success && <div className="alert alert-success">Product added successfully!</div>}

      <form onSubmit={handleSubmit} className="add-product-form">
        <div className="form-section">
          <h3>Product Details</h3>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="sku">SKU *</label>
              <input
                type="text"
                id="sku"
                name="sku"
                value={formData.sku}
                onChange={handleChange}
                required
                className="form-control"
                placeholder="e.g., CANN-250-VAF"
              />
            </div>
            <div className="form-group">
              <label htmlFor="product">Product Name *</label>
              <input
                type="text"
                id="product"
                name="product"
                value={formData.product}
                onChange={handleChange}
                required
                className="form-control"
                placeholder="e.g., Cannibal Ferox"
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="size">Size *</label>
              <input
                type="text"
                id="size"
                name="size"
                value={formData.size}
                onChange={handleChange}
                required
                className="form-control"
                placeholder="e.g., 20oz Can"
              />
            </div>
            <div className="form-group">
              <label htmlFor="flavor">Flavor *</label>
              <input
                type="text"
                id="flavor"
                name="flavor"
                value={formData.flavor}
                onChange={handleChange}
                required
                className="form-control"
                placeholder="e.g., Vanilla Frosting"
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="unitsCs">Units per Case *</label>
              <input
                type="text"
                id="unitsCs"
                name="unitsCs"
                value={formData.unitsCs}
                onChange={handleChange}
                required
                className="form-control"
                placeholder="e.g., 24"
              />
            </div>
            <div className="form-group">
              <label htmlFor="quantity">Initial Inventory Quantity</label>
              <input
                type="number"
                id="quantity"
                name="quantity"
                value={formData.quantity}
                onChange={handleChange}
                min="0"
                className="form-control"
                placeholder="0"
              />
            </div>
          </div>
        </div>

        <div className="form-section">
          <h3>Shipping Dimensions (Optional)</h3>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="length">Length (inches)</label>
              <input
                type="number"
                id="length"
                name="length"
                value={formData.length}
                onChange={handleChange}
                step="0.1"
                min="0"
                className="form-control"
                placeholder="0.0"
              />
            </div>
            <div className="form-group">
              <label htmlFor="width">Width (inches)</label>
              <input
                type="number"
                id="width"
                name="width"
                value={formData.width}
                onChange={handleChange}
                step="0.1"
                min="0"
                className="form-control"
                placeholder="0.0"
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="height">Height (inches)</label>
              <input
                type="number"
                id="height"
                name="height"
                value={formData.height}
                onChange={handleChange}
                step="0.1"
                min="0"
                className="form-control"
                placeholder="0.0"
              />
            </div>
            <div className="form-group">
              <label htmlFor="weight">Weight (lbs)</label>
              <input
                type="number"
                id="weight"
                name="weight"
                value={formData.weight}
                onChange={handleChange}
                step="0.1"
                min="0"
                className="form-control"
                placeholder="0.0"
              />
            </div>
          </div>
        </div>

        <div className="form-actions">
          <button 
            type="button" 
            className="btn btn-secondary"
            onClick={() => navigate('/inventory-settings')}
          >
            Cancel
          </button>
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? 'Adding Product...' : 'Add Product'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default AddProduct;