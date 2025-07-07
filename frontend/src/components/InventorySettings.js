import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FaBoxes, FaPlus, FaTrash, FaArrowLeft, FaEdit, FaDatabase } from 'react-icons/fa';
import './InventorySettings.css';

function InventorySettings() {
  const navigate = useNavigate();

  return (
    <div className="inventory-settings-container">
      <div className="settings-header">
        <button 
          className="back-button"
          onClick={() => navigate('/vieworders')}
        >
          <FaArrowLeft /> Back to Orders
        </button>
        <h2>Inventory Management</h2>
      </div>

      <div className="settings-grid">
        <div 
          className="settings-card"
          onClick={() => navigate('/updateinventory')}
        >
          <FaBoxes className="card-icon" />
          <h3>Update Inventory</h3>
          <p>Adjust current stock quantities for existing products</p>
        </div>

        <div 
          className="settings-card"
          onClick={() => navigate('/add-product')}
        >
          <FaPlus className="card-icon" />
          <h3>Add New Product</h3>
          <p>Create a new product with SKU, details, and shipping info</p>
        </div>

        <div 
          className="settings-card"
          onClick={() => navigate('/remove-product')}
        >
          <FaTrash className="card-icon" />
          <h3>Remove Product</h3>
          <p>Delete a product from the inventory system</p>
        </div>

        <div 
          className="settings-card"
          onClick={() => navigate('/edit-products')}
        >
          <FaEdit className="card-icon" />
          <h3>Edit Product Details</h3>
          <p>Edit product names, sizes, flavors, and shipping dimensions</p>
        </div>

        <div 
          className="settings-card"
          onClick={() => navigate('/delete-orders')}
        >
          <FaTrash className="card-icon" style={{ color: '#d32f2f' }} />
          <h3>Delete Test Orders</h3>
          <p>Permanently remove test orders from the system (admin only)</p>
        </div>

        <div 
          className="settings-card"
          onClick={() => navigate('/backup-database')}
        >
          <FaDatabase className="card-icon" style={{ color: '#17a2b8' }} />
          <h3>Backup Database</h3>
          <p>Email database backup to admin</p>
        </div>
      </div>
    </div>
  );
}

export default InventorySettings;