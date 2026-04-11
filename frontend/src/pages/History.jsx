import { useState, useEffect } from 'react';
import { getBill, downloadReceipt } from '../services/api';
import axios from 'axios';

function History() {
  const [bills,    setBills]    = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    axios.get('http://localhost:8000/billing/')
      .then(res => setBills(res.data.bills || []))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const toggleExpand = async (transactionId) => {
    if (expanded && expanded.transaction_id === transactionId) {
      setExpanded(null);
      return;
    }
    try {
      const res = await getBill(transactionId);
      setExpanded(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDownload = async (transactionId) => {
    try {
      const res = await downloadReceipt(transactionId);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a   = document.createElement('a');
      a.href    = url;
      a.download = 'receipt_' + transactionId + '.pdf';
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Could not download receipt.');
    }
  };

  if (loading) {
    return (
      <div>
        <h2 style={{ marginBottom: 20, color: '#1F3864' }}>History</h2>
        <div className="card">
          <p style={{ textAlign: 'center', color: '#64748b' }}>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2 style={{ marginBottom: 20, color: '#1F3864' }}>Transaction History</h2>

      {bills.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <div style={{ fontSize: 48 }}>[ ]</div>
            <p>No transactions yet</p>
            <p style={{ fontSize: 13, marginTop: 8 }}>Completed bills will appear here</p>
          </div>
        </div>
      ) : (
        <div>
          {bills.map((bill) => (
            <div key={bill.transaction_id} className="card" style={{ marginBottom: 12, padding: 0, overflow: 'hidden' }}>

              <div
                style={{
                  display: 'flex', justifyContent: 'space-between',
                  alignItems: 'center', padding: '16px 20px',
                  cursor: 'pointer', background: 'white'
                }}
                onClick={() => toggleExpand(bill.transaction_id)}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: 15, color: '#1F3864' }}>
                    Transaction #{bill.transaction_id}
                  </div>
                  <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>
                    {new Date(bill.created_at).toLocaleString()}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ fontWeight: 700, fontSize: 16, color: '#1F3864' }}>
                    Tk {bill.total_amount ? bill.total_amount.toFixed(2) : '0.00'}
                  </span>
                  <span style={{ color: '#94a3b8', fontSize: 12 }}>
                    {expanded && expanded.transaction_id === bill.transaction_id ? 'Hide' : 'View'}
                  </span>
                </div>
              </div>

              {expanded && expanded.transaction_id === bill.transaction_id && (
                <div style={{ borderTop: '1px solid #e2e8f0', padding: '16px 20px', background: '#f8faff' }}>
                  <table className="bill-table" style={{ marginBottom: 16 }}>
                    <thead>
                      <tr>
                        <th>Medicine</th>
                        <th style={{ textAlign: 'center' }}>Qty</th>
                        <th style={{ textAlign: 'right' }}>Unit Price</th>
                        <th style={{ textAlign: 'right' }}>Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {expanded.items.map((item, i) => (
                        <tr key={i}>
                          <td>{item.medicine_name}</td>
                          <td style={{ textAlign: 'center' }}>{item.quantity}</td>
                          <td style={{ textAlign: 'right' }}>Tk {item.unit_price ? item.unit_price.toFixed(2) : '0.00'}</td>
                          <td style={{ textAlign: 'right' }}>Tk {item.total_price ? item.total_price.toFixed(2) : '0.00'}</td>
                        </tr>
                      ))}
                      <tr className="bill-total-row">
                        <td colSpan="3" style={{ textAlign: 'right' }}>TOTAL</td>
                        <td style={{ textAlign: 'right' }}>Tk {expanded.total_amount ? expanded.total_amount.toFixed(2) : '0.00'}</td>
                      </tr>
                    </tbody>
                  </table>
                  <button
                    className="btn btn-primary"
                    onClick={() => handleDownload(bill.transaction_id)}
                  >
                    Download Receipt PDF
                  </button>
                </div>
              )}

            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default History;