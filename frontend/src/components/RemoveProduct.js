import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaArrowLeft, FaTrash } from 'react-icons/fa';
import { Modal, Button } from 'react-bootstrap';
import './RemoveProduct.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

function RemoveProduct({ onProductRemoved }) {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await fetch(`${API_URL}/api/products`, {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to fetch products');
      }

      const data = await response.json();
      setProducts(data);
    } catch (err) {
      setError('Failed to load products');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectProduct = (product) => {
    setSelectedProduct(product);
    setShowModal(true);
  };

  const handleDeleteConfirm = async () => {
    if (!selectedProduct) return;

    setDeleting(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/api/products/${selectedProduct.sku}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to delete product');
      }

      // Refresh the product list
      await fetchProducts();
      
      // Call parent callback if provided
      if (onProductRemoved) {
        onProductRemoved();
      }

      setShowModal(false);
      setSelectedProduct(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setDeleting(false);
    }
  };

  const filteredProducts = products.filter(product => {
    const search = searchTerm.toLowerCase();
    return product.sku.toLowerCase().includes(search) ||
           product.product.toLowerCase().includes(search) ||
           product.flavor.toLowerCase().includes(search);
  });

  if (loading) return <div className="loading">Loading products...</div>;

  return (
    <div className="remove-product-container">
      <div className="remove-product-header">
        <button 
          className="back-button"
          onClick={() => navigate('/inventory-settings')}
        >
          <FaArrowLeft /> Back to Settings
        </button>
        <h2>Remove Product</h2>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="product-search">
        <input
          type="text"
          className="form-control search-input"
          placeholder="Search by SKU, product name, or flavor..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="products-grid">
        {filteredProducts.length === 0 ? (
          <div className="no-products">
            {searchTerm ? 'No products match your search.' : 'No products available.'}
          </div>
        ) : (
          filteredProducts.map(product => (
            <div key={product.sku} className="product-card">
              <div className="product-info">
                <h4>{product.product}</h4>
                <p className="product-sku">SKU: {product.sku}</p>
                <p className="product-details">
                  {product.size} - {product.flavor}
                </p>
                <p className="product-units">
                  {product.unitsCs} units/case
                </p>
                {product.quantity !== undefined && (
                  <p className="product-quantity">
                    Current Stock: {product.quantity} cases
                  </p>
                )}
              </div>
              <button
                className="remove-button"
                onClick={() => handleSelectProduct(product)}
              >
                <FaTrash /> Remove
              </button>
            </div>
          ))
        )}
      </div>

      <Modal show={showModal} onHide={() => setShowModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Product Removal</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedProduct && (
            <div>
              <p>Are you sure you want to remove this product?</p>
              <div className="product-summary">
                <strong>{selectedProduct.product}</strong>
                <p>SKU: {selectedProduct.sku}</p>
                <p>{selectedProduct.size} - {selectedProduct.flavor}</p>
              </div>
              <div className="alert alert-warning mt-3">
                <strong>Warning:</strong> This action cannot be undone. All inventory data for this product will be permanently deleted.
              </div>
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)}>
            Cancel
          </Button>
          <Button 
            variant="danger" 
            onClick={handleDeleteConfirm}
            disabled={deleting}
          >
            {deleting ? 'Removing...' : 'Remove Product'}
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}

export default RemoveProduct;