import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './UpdateInventory.css';  // Create this file if it doesn't exist

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

function UpdateInventory({ onInventoryUpdated }) {
    const [inventory, setInventory] = useState([]);
    const [pendingChanges, setPendingChanges] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        fetchInventory();
    }, []);

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
            setLoading(false);
        } catch (err) {
            setError('Failed to fetch inventory');
            setLoading(false);
            console.error('Error:', err);
        }
    };

    const handleQuantityChange = (sku, newQuantity) => {
        setPendingChanges(prev => ({
            ...prev,
            [sku]: newQuantity
        }));
    };

    const submitChanges = async () => {
        try {
            const updatePromises = Object.entries(pendingChanges).map(([sku, quantity]) => 
                fetch(`${API_URL}/api/inventory/${sku}`, {
                    method: 'PUT',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ quantity }),
                }).then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
            );

            await Promise.all(updatePromises);
            await fetchInventory();
            setPendingChanges({});
            alert('Inventory updated successfully!');
            if (onInventoryUpdated) onInventoryUpdated();
        } catch (err) {
            console.error('Error updating inventory:', err);
            setError('Failed to update inventory');
        }
    };

    const hasChanges = Object.keys(pendingChanges).length > 0;

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;

    return (
        <div className="update-inventory-container">
            <h1>Update Inventory</h1>
            <table>
                <thead>
                    <tr>
                        <th>SKU</th>
                        <th>Product</th>
                        <th>Size</th>
                        <th>Flavor</th>
                        <th>Units/Case</th>
                        <th>Current Quantity</th>
                        <th>New Quantity</th>
                    </tr>
                </thead>
                <tbody>
                    {inventory.map((item) => (
                        <tr key={item.sku}>
                            <td>{item.sku}</td>
                            <td>{item.product}</td>
                            <td>{item.size}</td>
                            <td>{item.flavor}</td>
                            <td>{item.unitsCs}</td>
                            <td>{item.quantity}</td>
                            <td>
                                <input
                                    type="number"
                                    min="0"
                                    value={pendingChanges[item.sku] ?? item.quantity}
                                    onChange={(e) => handleQuantityChange(item.sku, parseInt(e.target.value))}
                                />
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
            <div className="button-container">
                <button 
                    className="back-button"
                    onClick={() => {
                        if (hasChanges) {
                            if (window.confirm('You have unsaved changes. Are you sure you want to leave?')) {
                                navigate('/');
                            }
                        } else {
                            navigate('/');
                        }
                    }}
                >
                    Back to Order Form
                </button>
                <button 
                    className="submit-button"
                    onClick={submitChanges}
                    disabled={!hasChanges}
                >
                    Submit Changes
                </button>
            </div>
        </div>
    );
}

export default UpdateInventory;
