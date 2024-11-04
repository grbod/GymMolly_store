import React, { useState, useEffect } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { Modal, Button } from 'react-bootstrap';
import OrderForm from './components/OrderForm';
import AddAddress from './components/AddAddress';
import UpdateAddress from './components/UpdateAddress';
import UpdateInventory from './components/UpdateInventory';
import OrderValidation from './components/OrderValidation';
import ViewOrders from './components/ViewOrders';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [formData, setFormData] = useState({
    po: '',
    address: null,
    products: [],
    shippingMethod: 'FedEx Ground'
  });
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [addresses, setAddresses] = useState([]);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchAddresses();
    fetchInventory();
  }, []);

  const fetchAddresses = async () => {
    try {
      const response = await fetch(`${API_URL}/api/shipping-addresses`);
      const data = await response.json();
      setAddresses(data);
    } catch (err) {
      console.error('Failed to fetch addresses:', err);
    }
  };

  const fetchInventory = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/inventory`);
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
          cases: 0
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
    
    // Navigate to order validation page
    navigate('/order-validation');
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
        cases: 0
      })),
      shippingMethod: 'FedEx Ground' // Reset shipping method to default
    });
  };

  if (loading) return <div>Loading inventory data...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="App container py-4 bg-light">
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
          />
        } />
        <Route path="/add-address" element={<AddAddress onAddressAdded={refreshAddresses} />} />
        <Route path="/edit-address/:id" element={<UpdateAddress onAddressUpdated={updateAddressInList} />} />
        <Route path="/updateinventory" element={<UpdateInventory onInventoryUpdated={fetchInventory} />} />
        <Route path="/order-validation" element={<OrderValidation orderData={formData} onConfirm={handleSubmit} onCancel={() => setShowValidation(false)} isSubmitting={isSubmitting} onOrderSuccess={resetFormData} />} />
        <Route path="/vieworders" element={<ViewOrders />} />
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
