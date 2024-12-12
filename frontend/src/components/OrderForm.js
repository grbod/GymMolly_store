import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function OrderForm({ 
  formData, 
  addresses, 
  inventory,
  handleInputChange, 
  handleCasesChange, 
  handleSubmit,
  handleDeleteClick,
  handleFileUpload,
  shippingMethods
}) {
  const navigate = useNavigate();

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles) => {
      // Simply store the files, no processing yet
      const updatedFiles = formData.attachment 
        ? [...formData.attachment, ...acceptedFiles]
        : acceptedFiles;
      handleFileUpload(updatedFiles);
    },
    multiple: true,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg']
    }
  });

  const handleFileRemove = (fileToRemove) => {
    const updatedFiles = formData.attachment.filter(file => file !== fileToRemove);
    handleFileUpload(updatedFiles);
  };

  return (
    <div className="card shadow-sm bg-white">
      <div className="card-body">
        <div className="d-flex justify-content-between align-items-start mb-4">
          <h1 className="text-primary">Gym Molly Order Form</h1>
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
                <div className="mt-2 d-grid gap-2">
                  <button 
                    type="button" 
                    className="btn btn-outline-primary"
                    onClick={() => navigate(`/edit-address/${formData.address.id}`)}
                  >
                    Edit Address
                  </button>
                  <button 
                    type="button" 
                    className="btn btn-danger"
                    onClick={handleDeleteClick}
                  >
                    Delete Address
                  </button>
                </div>
              </div>
            </div>
          )}

          <div className="mb-3">
            <Link to="/add-address" className="btn btn-outline-primary btn-sm">
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
                {formData.products.map((product) => (
                  <tr key={product.sku}>
                    <td>{product.product}</td>
                    <td>{product.size}</td>
                    <td>{product.flavor}</td>
                    <td>{product.unitsCs}</td>
                    <td>
                      <input
                        type="number"
                        className="form-control w-auto"
                        style={{ minWidth: '100px' }}
                        value={product.cases || ''}
                        onChange={(e) => handleCasesChange(product.sku, e.target.value)}
                        min="0"
                        max={inventory.find(item => item.sku === product.sku)?.quantity || 0}
                      />
                    </td>
                    <td>{inventory.find(item => item.sku === product.sku)?.quantity || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mb-3">
            <label className="form-label" style={{ color: '#000000' }}>
              Upload Pre-Created Shipping Labels
            </label>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
              <div 
                {...getRootProps()} 
                className="rounded p-4 text-center cursor-pointer"
                style={{ 
                  borderStyle: 'dashed',
                  cursor: 'pointer',
                  backgroundColor: isDragActive ? '#d4d7da' : '#e2e4e7',
                  border: '3px dashed #949494',
                  width: '160px',
                  height: '160px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '10px'
                }}
              >
                <input {...getInputProps()} />
                {isDragActive ? (
                  <p className="mb-0">Drop the files here...</p>
                ) : (
                  <p className="mb-0" style={{ fontSize: '0.9rem', lineHeight: '1.4' }}>
                    Drag & drop shipping<br />labels here,<br />or click to select
                    <br />
                    <small className="text-muted" style={{ fontSize: '0.8rem' }}>
                      (Upload PDF, PNG, JPG files)
                    </small>
                  </p>
                )}
              </div>
              {formData.attachment && formData.attachment.length > 0 && (
                <div className="mt-1" style={{ marginLeft: '5px' }}>
                  {/* Calculate total cases */}
                  {(() => {
                    const totalCases = formData.products.reduce((sum, product) => sum + (parseInt(product.cases) || 0), 0);
                    const numFiles = formData.attachment.length;
                    const isMatch = totalCases === numFiles;
                    
                    return (
                      <div style={{ marginBottom: '8px' }}>
                        <small style={{ 
                          color: isMatch ? '#198754' : '#dc3545',
                          fontWeight: 'bold'
                        }}>
                          #{numFiles} Labels Uploaded | {totalCases} Cases Selected - {isMatch ? 'MATCH' : 'NOT MATCH'}
                        </small>
                      </div>
                    );
                  })()}
                  
                  {formData.attachment.map(file => (
                    <div key={file.name} style={{ marginBottom: '4px' }}>
                      <small className="text-success" style={{ display: 'flex', alignItems: 'center' }}>
                        <span style={{ color: '#198754', marginRight: '4px' }}>✓</span>
                        <span>
                          File attached: {file.name}
                          <button
                            type="button"
                            className="btn btn-link btn-sm p-0 ms-2"
                            onClick={() => handleFileRemove(file)}
                            style={{ 
                              lineHeight: 1,
                              border: 'none',
                              background: 'none',
                              padding: 0,
                              display: 'inline-flex',
                              alignItems: 'center',
                              position: 'relative',
                              top: '0px'
                            }}
                            title="Remove file"
                          >
                            (<svg 
                              width="14" 
                              height="14" 
                              viewBox="0 0 24 24" 
                              fill="none" 
                              stroke="#dc3545" 
                              strokeWidth="2" 
                              strokeLinecap="round" 
                              strokeLinejoin="round"
                            >
                              <line x1="18" y1="6" x2="6" y2="18"></line>
                              <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>)
                          </button>
                        </span>
                      </small>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="mb-3">
            <label htmlFor="shippingMethod" className="form-label">Shipping Method</label>
            <select
              className="form-select"
              id="shippingMethod"
              name="shippingMethod"
              value={formData.shippingMethod}
              onChange={handleInputChange}
            >
              {shippingMethods.map((method) => (
                <option key={method} value={method}>
                  {method}
                </option>
              ))}
            </select>
          </div>

          <button type="submit" className="btn btn-primary">Submit</button>
          
          <div className="text-center mt-3">
            <button 
              type="button" 
              className="btn btn-secondary"
              onClick={() => navigate('/vieworders')}
            >
              View Order History
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default OrderForm;
