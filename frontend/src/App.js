import React, { useState, useEffect } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import { Routes, Route, useNavigate, Navigate } from 'react-router-dom';
import { Modal, Button } from 'react-bootstrap';
import Login from './components/Login';
import OrderForm from './components/OrderForm';
import AddAddress from './components/AddAddress';
import UpdateAddress from './components/UpdateAddress';
import UpdateInventory from './components/UpdateInventory';
import OrderValidation from './components/OrderValidation';
import ViewOrders from './components/ViewOrders';
import ShippingLabels from './components/ShippingLabels';
import InventorySettings from './components/InventorySettings';
import AddProduct from './components/AddProduct';
import RemoveProduct from './components/RemoveProduct';
import DeleteOrders from './components/DeleteOrders';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);
  const [formData, setFormData] = useState({
    po: '',
    address: null,
    products: [],
    attachment: [],
    shippingMethod: 'FedEx Ground'
  });
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [addresses, setAddresses] = useState([]);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const initializeApp = async () => {
      try {
        const response = await fetch(`${API_URL}/api/check-auth`, {
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        });
        const data = await response.json();
        
        if (data.authenticated) {
          setIsAuthenticated(true);
          // Fetch addresses and inventory in parallel
          await Promise.all([
            fetchAddresses(),
            fetchInventory()
          ]);
        } else {
          setIsAuthenticated(false);
          setLoading(false); // Fix: Set loading to false when not authenticated
        }
      } catch (err) {
        console.error('Auth check failed:', err);
        setIsAuthenticated(false);
        setLoading(false); // Fix: Set loading to false on error too
      } finally {
        setAuthLoading(false);
      }
    };
    
    initializeApp();
  }, []);


  const fetchAddresses = async () => {
    try {
      const response = await fetch(`${API_URL}/api/shipping-addresses`, {
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });
      const data = await response.json();
      setAddresses(data);
    } catch (err) {
      console.error('Failed to fetch addresses:', err);
    }
  };

  const fetchInventory = async () => {
    try {
      const response = await fetch(`${API_URL}/api/inventory`, {
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });
      const data = await response.json();
      setInventory(data);
      setFormData(prevState => ({
        ...prevState,
        products: data.map(item => ({
          sku: item.sku,
          product: item.product,
          size: item.size,
          flavor: item.flavor,
          unitsCs: item.unitsCs,
          cases: 0,
          dimensions: item.dimensions,
          weight: item.weight
        }))
      }));
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch inventory data');
      setLoading(false);
      console.error('Error fetching inventory:', err);
    }
  };

  const handleInputChange = (e) => {
    if (e.target.name === 'address') {
      const selectedAddress = addresses.find(addr => addr.id === parseInt(e.target.value));
      setFormData({ ...formData, [e.target.name]: selectedAddress || '' });
    } else {
      setFormData({ ...formData, [e.target.name]: e.target.value });
    }
  };

  const handleCasesChange = (sku, value) => {
    setFormData(prevState => ({
      ...prevState,
      products: prevState.products.map(product => {
        if (product.sku === sku) {
          // Ensure value is a number and not negative
          const newValue = Math.max(0, parseInt(value) || 0);
          // Get max available quantity
          const maxAvailable = inventory.find(item => item.sku === sku)?.quantity || 0;
          // Ensure value doesn't exceed available quantity
          const finalValue = Math.min(newValue, maxAvailable);
          return {
            ...product,
            cases: finalValue
          };
        }
        return product;
      })
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Check if there are any products with cases > 0
    const hasProducts = formData.products.some(product => product.cases > 0);
    
    if (!formData.po || !formData.address || !hasProducts) {
      alert('Please fill in all required fields (PO#, Address, and at least one product)');
      return;
    }
    
    // Navigate to shipping labels page
    navigate('/shipping-labels');
  };

  const refreshAddresses = () => {
    fetchAddresses();
  };

  const handleDeleteClick = () => {
    setShowDeleteModal(true);
  };

  const handleDeleteConfirm = async () => {
    if (!formData.address) return;

    try {
      const response = await fetch(`${API_URL}/api/shipping-addresses/${formData.address.id}`, {
        method: 'DELETE',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        setFormData({ ...formData, address: null });
        fetchAddresses();
        setShowDeleteModal(false);
      } else {
        console.error('Failed to delete address');
      }
    } catch (err) {
      console.error('Error deleting address:', err);
    }
  };

  const handleDeleteCancel = () => {
    setShowDeleteModal(false);
  };

  // Add this function to update a specific address in the addresses array
  const updateAddressInList = (updatedAddress) => {
    setAddresses(prevAddresses => 
      prevAddresses.map(addr => 
        addr.id === updatedAddress.id ? updatedAddress : addr
      )
    );
    // Also update the selected address if it's currently selected
    if (formData.address && formData.address.id === updatedAddress.id) {
      setFormData(prev => ({
        ...prev,
        address: updatedAddress
      }));
    }
  };

  // Update this function
  const resetFormData = async () => {
    // Refresh inventory first
    await fetchInventory();
    
    // Then reset the form with the new inventory data
    setFormData({
      po: '',
      address: null,
      products: inventory.map(item => ({
        sku: item.sku,
        product: item.product,
        size: item.size,
        flavor: item.flavor,
        unitsCs: item.unitsCs,
        cases: 0,
        dimensions: item.dimensions,
        weight: item.weight
      })),
      attachment: [],
      shippingMethod: 'FedEx Ground'
    });
  };

  // Add this function to handle file uploads
  const handleFileUpload = (acceptedFiles) => {
    if (acceptedFiles && acceptedFiles.length > 0) {
      setFormData(prev => ({
        ...prev,
        attachment: acceptedFiles
      }));
    }
  };

  const handleLogin = async (authenticated) => {
    setIsAuthenticated(authenticated);
    if (authenticated) {
      // Fetch data after successful login
      try {
        await Promise.all([
          fetchAddresses(),
          fetchInventory()
        ]);
      } catch (err) {
        console.error('Failed to fetch data after login:', err);
      }
    }
  };

  const handleLogout = async () => {
    try {
      await fetch(`${API_URL}/api/logout`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      setIsAuthenticated(false);
      navigate('/login');
    } catch (err) {
      console.error('Logout error:', err);
    }
  };

  if (authLoading || loading) return <div>Loading...</div>;
  
  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<Login onLogin={handleLogin} />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  if (error) return <div>Error: {error}</div>;

  return (
    <div className="App container py-4 bg-light">
      <div className="d-flex justify-content-end mb-3">
        <button 
          className="logout-button"
          onClick={handleLogout}
        >
          Logout
        </button>
      </div>
      <Routes>
        <Route path="/" element={
          <OrderForm 
            formData={formData}
            addresses={addresses}
            inventory={inventory}
            handleInputChange={handleInputChange}
            handleCasesChange={handleCasesChange}
            handleSubmit={handleSubmit}
            handleDeleteClick={handleDeleteClick}
            handleFileUpload={handleFileUpload}
          />
        } />
        <Route path="/add-address" element={<AddAddress onAddressAdded={refreshAddresses} />} />
        <Route path="/edit-address/:id" element={<UpdateAddress onAddressUpdated={updateAddressInList} />} />
        <Route path="/inventory-settings" element={<InventorySettings />} />
        <Route path="/updateinventory" element={<UpdateInventory onInventoryUpdated={fetchInventory} />} />
        <Route path="/add-product" element={<AddProduct onProductAdded={fetchInventory} />} />
        <Route path="/remove-product" element={<RemoveProduct onProductRemoved={fetchInventory} />} />
        <Route path="/delete-orders" element={<DeleteOrders onOrderDeleted={fetchInventory} />} />
        <Route path="/shipping-labels" element={
          <ShippingLabels 
            formData={formData}
            handleFileUpload={handleFileUpload}
            handleInputChange={handleInputChange}
            shippingMethods={[
              'FedEx Ground',
              'FedEx 2Day',
              'FedEx Express Saver'
            ]}
          />
        } />
        <Route path="/order-validation" element={<OrderValidation orderData={formData} onConfirm={handleSubmit} onCancel={() => navigate('/')} onOrderSuccess={resetFormData} />} />
        <Route path="/vieworders" element={
          <ViewOrders 
            onInventoryUpdate={fetchInventory}
          />
        } />
      </Routes>
      
      <Modal show={showDeleteModal} onHide={handleDeleteCancel} centered>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Deletion</Modal.Title>
        </Modal.Header>
        <Modal.Body>Are you sure you want to delete this address?</Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleDeleteCancel}>Cancel</Button>
          <Button variant="danger" onClick={handleDeleteConfirm}>Delete</Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}

export default App;
