import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { FaArrowRight } from 'react-icons/fa';
import './OrderForm.css';

function OrderForm({ 
  formData, 
  addresses, 
  inventory,
  handleInputChange, 
  handleCasesChange, 
  handleSubmit,
  handleDeleteClick,
  handleFileUpload
}) {
  const navigate = useNavigate();

  return (
    <div className="card shadow-sm bg-white">
      <div className="card-body">
        <div className="d-flex justify-content-between align-items-start mb-4">
          <h1 className="text-primary">Gym Molly Store</h1>
          <img 
            src={process.env.PUBLIC_URL + '/GymMollyLogo.jpg'} 
            alt="Gym Molly Logo" 
            style={{ width: '100px', height: 'auto' }}
          />
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label htmlFor="po" className="form-label">PO#</label>
            <input
              type="text"
              className="form-control"
              id="po"
              name="po"
              value={formData.po}
              onChange={handleInputChange}
            />
          </div>

          <div className="mb-3">
            <label htmlFor="address" className="form-label">Address</label>
            <select
              className="form-select"
              id="address"
              name="address"
              value={formData.address ? formData.address.id : ''}
              onChange={handleInputChange}
            >
              <option value="">Select an address</option>
              {addresses
                .sort((a, b) => a.nickname.localeCompare(b.nickname))
                .map((address) => (
                  <option key={address.id} value={address.id}>
                    {address.nickname}
                  </option>
                ))}
            </select>
          </div>

          {formData.address && (
            <div className="card mb-3 bg-light">
              <div className="card-body">
                <p className="mb-1">{formData.address.companyName}</p>
                <p className="mb-1">{formData.address.addressLine1}</p>
                {formData.address.addressLine2 && <p className="mb-1">{formData.address.addressLine2}</p>}
                <p className="mb-1">{`${formData.address.city}, ${formData.address.state} ${formData.address.zipCode}`}</p>
                <p className="mb-1">Phone: {formData.address.phone}</p>
                <p className="mb-1">Email: {formData.address.email}</p>
                <div className="mt-2 d-flex gap-2">
                  <button 
                    type="button" 
                    className="btn address-edit-button"
                    style={{ 
                      padding: '0.25rem 0.75rem', 
                      fontSize: '0.75rem',
                      borderRadius: '20px'
                    }}
                    onClick={() => navigate(`/edit-address/${formData.address.id}`)}
                  >
                    Edit Address
                  </button>
                  <button 
                    type="button" 
                    className="btn btn-danger"
                    style={{ 
                      padding: '0.25rem 0.75rem', 
                      fontSize: '0.75rem',
                      borderRadius: '20px'
                    }}
                    onClick={handleDeleteClick}
                  >
                    Delete Address
                  </button>
                </div>
              </div>
            </div>
          )}

          <div className="mb-3">
            <Link 
              to="/add-address" 
              className="btn address-add-button"
              style={{ 
                padding: '0.25rem 0.75rem', 
                fontSize: '0.75rem',
                borderRadius: '20px'
              }}
            >
              <i className="bi bi-plus-circle me-1"></i>Add New Address
            </Link>
          </div>

          <div className="table-responsive">
            <table className="table table-hover">
              <thead className="table-light">
                <tr>
                  <th>Product</th>
                  <th>Size</th>
                  <th>Flavor</th>
                  <th>Units/Cs</th>
                  <th>#Cases</th>
                  <th>Avail. Cases</th>
                </tr>
              </thead>
              <tbody>
                {formData.products
                  .sort((a, b) => {
                    // First sort by product name
                    const productCompare = a.product.localeCompare(b.product);
                    if (productCompare !== 0) return productCompare;
                    // If products are the same, sort by flavor
                    return a.flavor.localeCompare(b.flavor);
                  })
                  .map((product) => (
                  <tr key={product.sku}>
                    <td>{product.product}</td>
                    <td>{product.size}</td>
                    <td>{product.flavor}</td>
                    <td>{product.unitsCs}</td>
                    <td>
                      <input
                        type="number"
                        className={`form-control w-auto ${inventory.find(item => item.sku === product.sku)?.quantity === 0 ? 'input-disabled-zero' : ''}`}
                        style={{ 
                          minWidth: '100px',
                          backgroundColor: inventory.find(item => item.sku === product.sku)?.quantity === 0 ? '#E9ECEF' : '',
                          cursor: inventory.find(item => item.sku === product.sku)?.quantity === 0 ? 'not-allowed' : 'text'
                        }}
                        value={product.cases || ''}
                        onChange={(e) => handleCasesChange(product.sku, e.target.value)}
                        min="0"
                        max={inventory.find(item => item.sku === product.sku)?.quantity || 0}
                        disabled={inventory.find(item => item.sku === product.sku)?.quantity === 0}
                      />
                    </td>
                    <td className={inventory.find(item => item.sku === product.sku)?.quantity === 0 ? 'text-danger-muted' : ''}>
                      {inventory.find(item => item.sku === product.sku)?.quantity || 0}
                      {inventory.find(item => item.sku === product.sku)?.quantity === 0 && (
                        <span className="inventory-alert-icon">⚠️</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="d-flex justify-content-between align-items-center mt-4">
            <button 
              type="button" 
              className="btn btn-secondary"
              style={{ 
                padding: '0.375rem 0.75rem',
                fontSize: '1rem'
              }}
              onClick={() => navigate('/vieworders')}
            >
              View Order History
            </button>
            
            <button 
              type="submit" 
              className="btn next-button"
            >
              Next <FaArrowRight />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default OrderForm;
