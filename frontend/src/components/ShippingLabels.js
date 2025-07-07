import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';

function ShippingLabels({ 
  formData, 
  handleFileUpload,
  handleInputChange,
  shippingMethods
}) {
  const navigate = useNavigate();

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles) => {
      // Check if we already have files
      if (formData.attachment && formData.attachment.length > 0) {
        // Get the file type of existing files
        const existingType = formData.attachment[0].type.startsWith('image/') ? 'image' : 'pdf';
        
        // Check if new files match the existing type
        const invalidFiles = acceptedFiles.filter(file => {
          const newType = file.type.startsWith('image/') ? 'image' : 'pdf';
          return newType !== existingType;
        });
        
        if (invalidFiles.length > 0) {
          alert('All files must be the same type. You cannot mix PDF and image files. Please remove existing files first if you want to switch file types.');
          return;
        }
      } else if (acceptedFiles.length > 1) {
        // Check if all new files are the same type
        const firstType = acceptedFiles[0].type.startsWith('image/') ? 'image' : 'pdf';
        const mixedTypes = acceptedFiles.some(file => {
          const fileType = file.type.startsWith('image/') ? 'image' : 'pdf';
          return fileType !== firstType;
        });
        
        if (mixedTypes) {
          alert('All files must be the same type. Please upload either all PDFs or all images (PNG/JPG).');
          return;
        }
      }
      
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

  // Calculate total cases and get product details
  const orderedProducts = formData.products.filter(product => product.cases > 0);
  const totalCases = orderedProducts.reduce((sum, product) => sum + parseInt(product.cases), 0);
  const numFiles = formData.attachment ? formData.attachment.length : 0;
  const isMatch = totalCases === numFiles;

  const handleBack = () => {
    navigate('/');
  };

  const handleContinue = (e) => {
    e.preventDefault();
    
    // Validate that we have the correct number of labels
    if (!isMatch) {
      alert(`Please upload exactly ${totalCases} shipping label(s) to match the number of cases ordered.`);
      return;
    }

    // Navigate to order validation
    navigate('/order-validation');
  };

  return (
    <div className="card shadow-sm bg-white">
      <div className="card-body">
        <div className="d-flex justify-content-between align-items-start mb-4">
          <h1 className="text-primary">Upload Shipping Labels</h1>
          <img 
            src={process.env.PUBLIC_URL + '/GymMollyLogo.jpg'} 
            alt="Gym Molly Logo" 
            style={{ width: '100px', height: 'auto' }}
          />
        </div>

        <div className="row mb-4">
          <div className="col-md-6">
            <div className="card bg-light">
              <div className="card-body">
                <h6 className="card-subtitle mb-2 text-muted">Purchase Order</h6>
                <p className="card-text fw-bold">{formData.po}</p>
              </div>
            </div>
          </div>
          <div className="col-md-6">
            <div className="card bg-light">
              <div className="card-body">
                <h6 className="card-subtitle mb-2 text-muted">Shipping Address</h6>
                <p className="card-text mb-1 fw-bold">{formData.address.nickname}</p>
                <p className="card-text mb-0">{formData.address.companyName}</p>
                <p className="card-text mb-0">{formData.address.addressLine1}</p>
                {formData.address.addressLine2 && <p className="card-text mb-0">{formData.address.addressLine2}</p>}
                <p className="card-text mb-0">{`${formData.address.city}, ${formData.address.state} ${formData.address.zipCode}`}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="mb-4">
          <h5>Please upload labels for the following items:</h5>
          <ul className="list-group mb-3">
            {orderedProducts.map((product) => (
              <li key={product.sku} className="list-group-item">
                <strong>{product.cases} {product.cases === 1 ? 'case' : 'cases'}</strong> of {product.product} - {product.flavor} ({product.size})
                {product.dimensions && product.weight && (
                  <span className="text-muted"> [{product.dimensions.length}"x{product.dimensions.width}"x{product.dimensions.height}", {product.weight} lbs/case]</span>
                )}
              </li>
            ))}
          </ul>
          <div className="alert alert-info">
            <strong>You need to upload {totalCases} label{totalCases !== 1 ? 's' : ''}</strong>
          </div>
        </div>

        <form onSubmit={handleContinue}>
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
                  <div style={{ marginBottom: '8px' }}>
                    <small style={{ 
                      color: isMatch ? '#198754' : '#dc3545',
                      fontWeight: 'bold'
                    }}>
                      #{numFiles} Labels Uploaded | {totalCases} Cases Selected - {isMatch ? 'MATCH' : 'NOT MATCH'}
                    </small>
                  </div>
                  
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

          <div className="mb-4">
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

          <div className="d-flex justify-content-between">
            <button 
              type="button"
              onClick={handleBack}
              className="btn btn-secondary"
            >
              Back
            </button>
            <button 
              type="submit" 
              className="btn" 
              style={{ 
                backgroundColor: '#B2CFEC',
                color: 'black',
                border: 'none'
              }}
              disabled={!isMatch}
            >
              Continue to Order Review
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ShippingLabels;