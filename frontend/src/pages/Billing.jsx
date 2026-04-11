import { useEffect, useState } from 'react';

function Billing() {
  const [bill, setBill] = useState(null);

  useEffect(() => {
    const saved = localStorage.getItem('lastBill');
    if (saved) setBill(JSON.parse(saved));
  }, []);

  const handlePrint = () => window.print();

  const handleNewBill = () => {
    localStorage.removeItem('lastBill');
    window.location.href = '/scan';
  };

  if (!bill) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px', color: '#94a3b8' }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>🧾</div>
        <h3 style={{ color: '#1F3864', marginBottom: 8 }}>No bill to show</h3>
        <p style={{ marginBottom: 24 }}>Go to Scan page to create a bill first.</p>
        <button className="btn btn-primary"
          onClick={() => window.location.href = '/scan'}>
          Go to Scan
        </button>
      </div>
    );
  }

  const subtotal       = bill.items?.reduce((sum, item) => sum + (item.total_price || 0), 0) || 0;
  const discountAmount = subtotal - (bill.total_amount || 0);

  return (
    <div>
      {/* Screen buttons — hidden when printing */}
      <div className="no-print" style={{
        display: 'flex', justifyContent: 'space-between',
        alignItems: 'center', marginBottom: 20
      }}>
        <h2 style={{ color: '#1F3864' }}>🧾 Bill Ready to Print</h2>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-success"
            onClick={handlePrint}
            style={{ fontSize: 16, padding: '10px 28px' }}>
            🖨️ Print
          </button>
          <button className="btn btn-primary" onClick={handleNewBill}>
            New Bill
          </button>
        </div>
      </div>

      {/* Bill content */}
      <div className="bill-print-area card" style={{ maxWidth: 480, margin: '0 auto', padding: 32 }}>

        {/* Header */}
        <div style={{
          textAlign: 'center',
          borderBottom: '2px dashed #1F3864',
          paddingBottom: 16, marginBottom: 16
        }}>
          <h1 style={{ fontSize: 26, fontWeight: 800, color: '#1F3864', letterSpacing: 2 }}>
            MediScan BD
          </h1>
          <p style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
            Smart Pharmacy Billing System
          </p>
        </div>

        {/* Transaction info */}
        <div style={{ marginBottom: 16, fontSize: 13, color: '#475569' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <span>Transaction ID</span>
            <span style={{ fontWeight: 600 }}>#{bill.transaction_id}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Date & Time</span>
            <span style={{ fontWeight: 600 }}>
              {new Date(bill.created_at).toLocaleString('en-BD')}
            </span>
          </div>
        </div>

        {/* Items table */}
        <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: 16, fontSize: 13 }}>
          <thead>
            <tr style={{ background: '#1F3864', color: 'white' }}>
              <th style={{ padding: '8px 10px', textAlign: 'left' }}>Medicine</th>
              <th style={{ padding: '8px 10px', textAlign: 'center' }}>Qty</th>
              <th style={{ padding: '8px 10px', textAlign: 'right' }}>Price</th>
              <th style={{ padding: '8px 10px', textAlign: 'right' }}>Total</th>
            </tr>
          </thead>
          <tbody>
            {bill.items?.map((item, index) => (
              <tr key={index} style={{ background: index % 2 === 0 ? '#f8faff' : 'white' }}>
                <td style={{ padding: '8px 10px', borderBottom: '1px solid #e2e8f0' }}>
                  {item.medicine_name}
                </td>
                <td style={{ padding: '8px 10px', textAlign: 'center', borderBottom: '1px solid #e2e8f0' }}>
                  {item.quantity}
                </td>
                <td style={{ padding: '8px 10px', textAlign: 'right', borderBottom: '1px solid #e2e8f0' }}>
                  ৳{(item.unit_price || 0).toFixed(2)}
                </td>
                <td style={{ padding: '8px 10px', textAlign: 'right', borderBottom: '1px solid #e2e8f0', fontWeight: 600 }}>
                  ৳{(item.total_price || 0).toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Totals */}
        <div style={{ borderTop: '2px solid #1F3864', paddingTop: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: '#64748b', marginBottom: 6 }}>
            <span>Subtotal</span>
            <span>৳{subtotal.toFixed(2)}</span>
          </div>
          {discountAmount > 0 && (
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: '#16a34a', marginBottom: 6 }}>
              <span>Discount</span>
              <span>− ৳{discountAmount.toFixed(2)}</span>
            </div>
          )}
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 22, fontWeight: 800, color: '#1F3864', marginTop: 8 }}>
            <span>TOTAL</span>
            <span>৳{(bill.total_amount || 0).toFixed(2)}</span>
          </div>
        </div>

        {/* Footer */}
        <div style={{ textAlign: 'center', borderTop: '2px dashed #1F3864', paddingTop: 16, marginTop: 20, fontSize: 12, color: '#64748b' }}>
          <p>Thank you for your purchase!</p>
          <p style={{ marginTop: 4 }}>Powered by MediScan BD</p>
        </div>
      </div>

      <style>{`
        @media print {
          .no-print  { display: none !important; }
          .navbar    { display: none !important; }
          .main-content { padding: 0 !important; max-width: 100% !important; }
          .bill-print-area { box-shadow: none !important; border: none !important; max-width: 100% !important; padding: 0 !important; }
          body { background: white !important; }
        }
      `}</style>
    </div>
  );
}

export default Billing;