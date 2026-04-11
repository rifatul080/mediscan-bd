import { useState, useRef, useEffect } from 'react';
import Webcam from 'react-webcam';
import { searchMedicine, createBill } from '../services/api';

function Scan() {
  const webcamRef     = useRef(null);
  const lastImageRef  = useRef(null);
  const intervalRef   = useRef(null);
  const ocrQueueRef   = useRef([]);
  const isOcrRunning  = useRef(false);

  const [cameraOn,     setCameraOn]     = useState(false);
  const [flash,        setFlash]        = useState(false);
  const [statusMsg,    setStatusMsg]    = useState('');
  const [suggestions,  setSuggestions]  = useState([]);
  const [manualQuery,  setManualQuery]  = useState('');
  const [searching,    setSearching]    = useState(false);
  const [devices,      setDevices]      = useState([]);
  const [deviceId,     setDeviceId]     = useState('');
  const [ocrPending,   setOcrPending]   = useState(0);

  const [billItems,       setBillItems]       = useState([]);
  const [discountPercent, setDiscountPercent] = useState('');
  const [discountFlat,    setDiscountFlat]    = useState('');
  const [submitting,      setSubmitting]      = useState(false);

  useEffect(() => {
    const saved = JSON.parse(localStorage.getItem('currentBill') || '[]');
    setBillItems(saved);
  }, []);

  useEffect(() => {
    navigator.mediaDevices.enumerateDevices().then(devs => {
      const cameras = devs.filter(d => d.kind === 'videoinput');
      setDevices(cameras);
      if (cameras.length > 0) setDeviceId(cameras[0].deviceId);
    });
  }, []);

  const saveBill = (items) => {
    localStorage.setItem('currentBill', JSON.stringify(items));
  };

  const triggerFlash = () => {
    setFlash(true);
    setTimeout(() => setFlash(false), 700);
  };

  const runNextOcr = async () => {
    if (isOcrRunning.current) return;
    if (ocrQueueRef.current.length === 0) return;
    isOcrRunning.current = true;
    const imageSrc = ocrQueueRef.current.shift();
    setOcrPending(ocrQueueRef.current.length);
    try {
      const response = await fetch('http://localhost:8000/detect/ocr', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ image: imageSrc })
      });
      const data = await response.json();
      console.log('OCR Result:', data);
      if (data.results && data.results.length > 0) {
        setSuggestions(prev => {
          const existing = [...prev];
          data.results.forEach(newResult => {
            if (!existing.find(r => r.id === newResult.id))
              existing.push({ ...newResult });
          });
          return existing;
        });
      }
    } catch (err) {
      console.error('OCR error:', err);
    }
    isOcrRunning.current = false;
    if (ocrQueueRef.current.length > 0) {
      setOcrPending(ocrQueueRef.current.length);
      setTimeout(() => runNextOcr(), 100);
    } else {
      setOcrPending(0);
    }
  };

  const addToOcrQueue = (imageSrc) => {
    ocrQueueRef.current.push(imageSrc);
    setOcrPending(ocrQueueRef.current.length);
    runNextOcr();
  };

  const startAutoCapture = () => {
    clearInterval(intervalRef.current);
    lastImageRef.current = null;
    let stableCount = 0;
    let motionSeen  = false;
    let emptyFrames = 0;
    console.log('Auto capture started!');

    intervalRef.current = setInterval(() => {
      const webcam = webcamRef.current;
      if (!webcam) return;
      const currentImage = webcam.getScreenshot();
      if (!currentImage) return;
      const prev = lastImageRef.current;
      lastImageRef.current = currentImage;
      if (!prev) return;

      try {
        const canvas1 = document.createElement('canvas');
        const canvas2 = document.createElement('canvas');
        const ctx1    = canvas1.getContext('2d');
        const ctx2    = canvas2.getContext('2d');
        canvas1.width = canvas2.width  = 64;
        canvas1.height = canvas2.height = 64;
        const img1 = new Image();
        const img2 = new Image();
        img1.onload = () => {
          ctx1.drawImage(img1, 0, 0, 64, 64);
          img2.onload = () => {
            ctx2.drawImage(img2, 0, 0, 64, 64);
            const data1 = ctx1.getImageData(0, 0, 64, 64).data;
            const data2 = ctx2.getImageData(0, 0, 64, 64).data;
            let diff = 0;
            for (let i = 0; i < data1.length; i += 4)
              diff += Math.abs(data1[i] - data2[i]);
            const avgDiff = diff / (data1.length / 4);
            console.log('avgDiff: ' + avgDiff.toFixed(1) + ' | stable: ' + stableCount);

            if (avgDiff > 20) {
              motionSeen = true; stableCount = 0; emptyFrames = 0;
              setStatusMsg('Hold still...');
            }
            if (avgDiff < 4 && motionSeen) {
              stableCount++;
              setStatusMsg('Almost there... ' + stableCount + '/2');
            }
            if (avgDiff > 20 && stableCount > 0) {
              stableCount = 0;
              setStatusMsg('Moved — hold still again');
            }
            if (avgDiff < 2) {
              emptyFrames++;
              if (emptyFrames > 5) {
                motionSeen = false; stableCount = 0; emptyFrames = 0;
                setStatusMsg('Hold a medicine up to start...');
              }
            } else { emptyFrames = 0; }

            if (stableCount >= 2) {
              stableCount = 0; motionSeen = false; emptyFrames = 0;
              lastImageRef.current = null;
              triggerFlash();
              setStatusMsg('CAPTURED! Hold next medicine...');
              console.log('Captured!');
              addToOcrQueue(currentImage);
              setTimeout(() => setStatusMsg('Hold next medicine up...'), 1000);
            }
          };
          img2.src = currentImage;
        };
        img1.src = prev;
      } catch (err) {
        console.error('Comparison error:', err);
      }
    }, 600);
  };

  const toggleCamera = () => {
    if (cameraOn) {
      clearInterval(intervalRef.current);
      setCameraOn(false);
      setStatusMsg('');
      ocrQueueRef.current  = [];
      isOcrRunning.current = false;
      setOcrPending(0);
    } else {
      setCameraOn(true);
      setStatusMsg('Hold a medicine up to start...');
    }
  };

  useEffect(() => {
    if (cameraOn) {
      const timer = setTimeout(() => startAutoCapture(), 1500);
      return () => { clearTimeout(timer); clearInterval(intervalRef.current); };
    }
  }, [cameraOn]);

  const handleManualSearch = async () => {
    if (!manualQuery.trim()) return;
    setSearching(true);
    try {
      const res = await searchMedicine(manualQuery);
      const results = res.data.results || [];
      setSuggestions(prev => {
        const existing = [...prev];
        results.forEach(r => {
          if (!existing.find(e => e.id === r.id)) existing.push(r);
        });
        return existing;
      });
    } catch (err) {
      console.error('Search error:', err);
    } finally {
      setSearching(false);
      setManualQuery('');
    }
  };

  const addToBill = (medicine) => {
    const updated  = [...billItems];
    const existing = updated.find(m => m.medicine_id === medicine.id);
    if (existing) {
      existing.quantity += 1;
    } else {
      updated.push({
        medicine_id:   medicine.id,
        medicine_name: (medicine.brand_name + ' ' + (medicine.strength || '')).trim(),
        manufacturer:  medicine.manufacturer,
        unit_price:    medicine.unit_price || 0,
        quantity:      1,
        use_per_unit:  false
      });
    }
    setBillItems(updated);
    saveBill(updated);
    setSuggestions(prev => prev.filter(s => s.id !== medicine.id));
  };

  const removeSuggestion = (id) =>
    setSuggestions(prev => prev.filter(s => s.id !== id));

  const subtotal = billItems.reduce(
    (sum, item) => sum + (item.unit_price || 0) * item.quantity, 0
  );
  const discountAmount = discountPercent
    ? subtotal * parseFloat(discountPercent) / 100
    : discountFlat ? parseFloat(discountFlat) || 0 : 0;
  const total = Math.max(0, subtotal - discountAmount);

  const updateQuantity = (index, qty) => {
    const updated = [...billItems];
    updated[index].quantity = Math.max(1, parseInt(qty) || 1);
    setBillItems(updated);
    saveBill(updated);
  };

  const removeItem = (index) => {
    const updated = billItems.filter((_, i) => i !== index);
    setBillItems(updated);
    saveBill(updated);
  };

  const clearBill = () => {
    setBillItems([]);
    localStorage.removeItem('currentBill');
    setDiscountPercent('');
    setDiscountFlat('');
  };

  const submitBill = async () => {
    if (billItems.length === 0) return;
    setSubmitting(true);
    try {
      const payload = {
        items: billItems.map(item => ({
          medicine_id:  item.medicine_id,
          quantity:     item.quantity,
          use_per_unit: item.use_per_unit || false
        })),
        discount_percent: discountPercent ? parseFloat(discountPercent) : null,
        discount_flat:    discountFlat    ? parseFloat(discountFlat)    : null,
      };
      const res = await createBill(payload);
      localStorage.setItem('lastBill', JSON.stringify(res.data));
      clearBill();
      window.location.href = '/billing';
    } catch (err) {
      alert('Error creating bill. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const badgeClass = (score) => {
    if (score >= 85) return 'confidence-badge high';
    if (score >= 65) return 'confidence-badge mid';
    return 'confidence-badge';
  };

  const cardHeader = (bg) => ({
    background: bg, color: 'white',
    margin: '-24px -24px 16px -24px',
    padding: '12px 20px',
    borderRadius: '10px 10px 0 0',
    fontSize: 15, fontWeight: 700,
    display: 'flex', alignItems: 'center', gap: 8
  });

  return (
    <div style={{ paddingBottom: 40 }}>
      <h2 style={{ marginBottom: 16, color: '#1F3864' }}>Scan Medicine</h2>

      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>

        {/* ── LEFT: Camera + Manual Search only ────── */}
        <div style={{ flex: '0 0 380px' }}>

          <div className="card" style={{ padding: 16 }}>
            <div style={cardHeader('#1F3864')}>
              Camera Detection
            </div>

            {!cameraOn && devices.length > 0 && (
              <div style={{ marginBottom: 10 }}>
                <label style={{ fontSize: 12, color: '#475569', fontWeight: 600 }}>
                  Select Camera:
                </label>
                <select value={deviceId}
                  onChange={e => setDeviceId(e.target.value)}
                  style={{
                    width: '100%', marginTop: 4, padding: '7px 10px',
                    border: '2px solid #e2e8f0', borderRadius: 8,
                    fontSize: 13, outline: 'none', background: 'white'
                  }}>
                  {devices.map((d, i) => (
                    <option key={d.deviceId} value={d.deviceId}>
                      {d.label || 'Camera ' + (i + 1)}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div style={{
              position: 'relative', width: '100%',
              paddingBottom: '75%', background: '#1a1a2e',
              borderRadius: 10, overflow: 'hidden'
            }}>
              {cameraOn ? (
                <>
                  {flash && (
                    <div style={{
                      position: 'absolute', inset: 0, zIndex: 10,
                      background: 'rgba(52,211,153,0.7)',
                      display: 'flex', alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 22, fontWeight: 700, color: 'white'
                    }}>
                      CAPTURED!
                    </div>
                  )}
                  <Webcam
                    ref={webcamRef}
                    screenshotFormat="image/jpeg"
                    screenshotQuality={0.85}
                    videoConstraints={{
                      deviceId: deviceId ? { exact: deviceId } : undefined,
                      width: 640, height: 480
                    }}
                    style={{
                      position: 'absolute', inset: 0,
                      width: '100%', height: '100%',
                      objectFit: 'cover'
                    }}
                  />
                  <div style={{
                    position: 'absolute', inset: 0,
                    display: 'flex', alignItems: 'center',
                    justifyContent: 'center', pointerEvents: 'none'
                  }}>
                    <div style={{
                      width: '70%', height: '65%',
                      border: '3px solid ' + (flash ? '#34d399' : '#60a5fa'),
                      borderRadius: 10,
                      boxShadow: '0 0 0 9999px rgba(0,0,0,0.35)',
                      transition: 'border-color 0.2s'
                    }} />
                  </div>
                  <div style={{
                    position: 'absolute', bottom: 8,
                    left: '50%', transform: 'translateX(-50%)',
                    background: 'rgba(0,0,0,0.75)',
                    color: statusMsg.includes('CAPTURED') ? '#34d399' :
                           statusMsg.includes('Almost')   ? '#60a5fa' :
                           statusMsg.includes('Hold still') ? '#fbbf24' : '#e2e8f0',
                    padding: '5px 14px', borderRadius: 20,
                    fontSize: 12, fontWeight: 600, whiteSpace: 'nowrap'
                  }}>
                    {statusMsg}
                  </div>
                </>
              ) : (
                <div style={{
                  position: 'absolute', inset: 0,
                  display: 'flex', flexDirection: 'column',
                  alignItems: 'center', justifyContent: 'center',
                  color: '#475569', gap: 8
                }}>
                  <span style={{ fontSize: 36 }}>[ ]</span>
                  <span style={{ fontSize: 13 }}>Camera is off</span>
                </div>
              )}
            </div>

            {ocrPending > 0 && (
              <div style={{
                marginTop: 8, padding: '6px 12px',
                background: '#fef3c7', borderRadius: 8,
                fontSize: 12, color: '#92400e',
                border: '1px solid #fde68a', textAlign: 'center'
              }}>
                Processing {ocrPending} image{ocrPending > 1 ? 's' : ''}...
              </div>
            )}

            <div style={{ marginTop: 10 }}>
              <button
                className={'btn ' + (cameraOn ? 'btn-danger' : 'btn-primary')}
                onClick={toggleCamera}
                style={{ width: '100%' }}
              >
                {cameraOn ? 'Stop Camera' : 'Start Camera'}
              </button>
            </div>

            {cameraOn && (
              <div style={{
                marginTop: 8, padding: '7px 10px',
                background: '#f0f9ff', borderRadius: 8,
                fontSize: 11, color: '#0369a1', border: '1px solid #bae6fd'
              }}>
                Hold medicine still in the blue frame — captures automatically
              </div>
            )}
          </div>

          <div className="card" style={{ padding: 16 }}>
            <div style={cardHeader('#475569')}>
              Manual Search
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <input
                type="text"
                placeholder="Type medicine name..."
                value={manualQuery}
                onChange={e => setManualQuery(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleManualSearch()}
                style={{
                  flex: 1, padding: '9px 12px',
                  border: '2px solid #e2e8f0',
                  borderRadius: 8, fontSize: 13, outline: 'none'
                }}
              />
              <button className="btn btn-primary"
                onClick={handleManualSearch} disabled={searching}
                style={{ padding: '9px 16px' }}>
                {searching ? '...' : 'Search'}
              </button>
            </div>
          </div>
        </div>

        {/* ── RIGHT: Live Bill + Suggestions below ─── */}
        <div style={{ flex: 1, minWidth: 0 }}>

          {/* Live Bill */}
          <div className="card" style={{
            padding: 16, border: '2px solid #1F3864', marginBottom: 20
          }}>
            <div style={cardHeader('#1F3864')}>
              Live Bill
              {billItems.length > 0 && (
                <span style={{
                  fontSize: 12, background: 'rgba(255,255,255,0.25)',
                  padding: '2px 8px', borderRadius: 20
                }}>
                  {billItems.length} item{billItems.length > 1 ? 's' : ''}
                </span>
              )}
            </div>

            {billItems.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '20px 0', color: '#94a3b8' }}>
                <div style={{ fontSize: 28 }}>[ ]</div>
                <p style={{ fontSize: 13, marginTop: 6 }}>No medicines added yet</p>
                <p style={{ fontSize: 11, color: '#cbd5e1', marginTop: 4 }}>
                  Scan or search a medicine to begin
                </p>
              </div>
            ) : (
              <>
                <div style={{ maxHeight: 260, overflowY: 'auto', marginBottom: 10 }}>
                  {billItems.map((item, index) => (
                    <div key={index} style={{
                      display: 'flex', alignItems: 'center',
                      padding: '7px 2px', borderBottom: '1px solid #f1f5f9', gap: 6
                    }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{
                          fontWeight: 600, fontSize: 13,
                          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'
                        }}>
                          {item.medicine_name}
                        </div>
                        <div style={{ fontSize: 11, color: '#64748b' }}>
                          Tk {item.unit_price?.toFixed(2)} each
                        </div>
                      </div>
                      <input type="number" min="1" value={item.quantity}
                        onChange={e => updateQuantity(index, e.target.value)}
                        style={{
                          width: 44, textAlign: 'center', padding: '3px 4px',
                          border: '2px solid #e2e8f0', borderRadius: 6, fontSize: 13
                        }}
                      />
                      <div style={{
                        fontWeight: 700, fontSize: 13, color: '#1F3864',
                        minWidth: 64, textAlign: 'right'
                      }}>
                        Tk {((item.unit_price || 0) * item.quantity).toFixed(2)}
                      </div>
                      <button onClick={() => removeItem(index)} style={{
                        background: 'none', border: 'none',
                        color: '#dc2626', cursor: 'pointer', fontSize: 18, padding: '0 2px'
                      }}>x</button>
                    </div>
                  ))}
                </div>

                <div style={{
                  background: '#f8faff', borderRadius: 8,
                  padding: '8px 12px', marginBottom: 10, border: '1px solid #e2e8f0'
                }}>
                  <div style={{
                    fontSize: 11, fontWeight: 700, color: '#475569',
                    marginBottom: 6, textTransform: 'uppercase'
                  }}>
                    Discount (Optional)
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 11, color: '#64748b', marginBottom: 2 }}>% Off</div>
                      <input type="number" placeholder="e.g. 10"
                        value={discountPercent} min="0" max="100"
                        onChange={e => { setDiscountPercent(e.target.value); setDiscountFlat(''); }}
                        style={{
                          width: '100%', padding: '6px 8px',
                          border: '2px solid #e2e8f0', borderRadius: 6, fontSize: 13, outline: 'none'
                        }}
                      />
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 11, color: '#64748b', marginBottom: 2 }}>Flat Tk Off</div>
                      <input type="number" placeholder="e.g. 50"
                        value={discountFlat} min="0"
                        onChange={e => { setDiscountFlat(e.target.value); setDiscountPercent(''); }}
                        style={{
                          width: '100%', padding: '6px 8px',
                          border: '2px solid #e2e8f0', borderRadius: 6, fontSize: 13, outline: 'none'
                        }}
                      />
                    </div>
                  </div>
                </div>

                <div style={{
                  background: '#f0f4ff', borderRadius: 8,
                  padding: '10px 12px', marginBottom: 12, border: '1px solid #c7d2fe'
                }}>
                  <div style={{
                    display: 'flex', justifyContent: 'space-between',
                    fontSize: 13, color: '#64748b', marginBottom: 4
                  }}>
                    <span>Subtotal</span><span>Tk {subtotal.toFixed(2)}</span>
                  </div>
                  {discountAmount > 0 && (
                    <div style={{
                      display: 'flex', justifyContent: 'space-between',
                      fontSize: 13, color: '#16a34a', marginBottom: 4
                    }}>
                      <span>Discount</span><span>- Tk {discountAmount.toFixed(2)}</span>
                    </div>
                  )}
                  <div style={{
                    display: 'flex', justifyContent: 'space-between',
                    fontSize: 22, fontWeight: 800, color: '#1F3864',
                    borderTop: '2px solid #1F3864', paddingTop: 8, marginTop: 6
                  }}>
                    <span>TOTAL</span><span>Tk {total.toFixed(2)}</span>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn btn-success"
                    style={{ flex: 1, fontSize: 14 }}
                    onClick={submitBill} disabled={submitting}>
                    {submitting ? 'Processing...' : 'Confirm Bill'}
                  </button>
                  <button className="btn btn-danger" onClick={clearBill}>Clear</button>
                </div>
              </>
            )}
          </div>

          {/* Suggestions — RIGHT column, BELOW Live Bill */}
          {suggestions.length > 0 && (
            <div className="card" style={{ padding: 16 }}>
              <div style={cardHeader('#16a34a')}>
                Suggestions
                <span style={{
                  fontSize: 12, background: 'rgba(255,255,255,0.25)',
                  padding: '2px 8px', borderRadius: 20
                }}>
                  {suggestions.length} found
                </span>
                {ocrPending > 0 && (
                  <span style={{
                    fontSize: 11, marginLeft: 'auto',
                    background: 'rgba(255,255,255,0.2)',
                    padding: '2px 8px', borderRadius: 20
                  }}>
                    +{ocrPending} processing
                  </span>
                )}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {suggestions.map((med, index) => (
                  <div key={med.id} style={{
                    border: '2px solid ' + (index === 0 ? '#16a34a' : '#e2e8f0'),
                    borderRadius: 10, padding: '10px 12px',
                    background: index === 0 ? '#f0fdf4' : 'white',
                    display: 'flex', alignItems: 'center', gap: 10
                  }}>
                    <div style={{
                      width: 28, height: 28, borderRadius: '50%',
                      background: index === 0 ? '#16a34a' : '#e2e8f0',
                      color: index === 0 ? 'white' : '#64748b',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 13, fontWeight: 700, flexShrink: 0
                    }}>
                      {index + 1}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 700, fontSize: 14 }}>
                        {med.brand_name}
                        {med.strength && (
                          <span style={{ fontWeight: 400, color: '#64748b', fontSize: 12 }}>
                            {' '}{med.strength}
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: 11, color: '#94a3b8' }}>{med.manufacturer}</div>
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <div style={{ fontWeight: 700, color: '#1F3864', fontSize: 15 }}>
                        {med.unit_price ? 'Tk ' + med.unit_price : 'N/A'}
                      </div>
                      <span className={badgeClass(med.confidence)} style={{ fontSize: 11 }}>
                        {Math.round(med.confidence)}%
                      </span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flexShrink: 0 }}>
                      <button className="btn btn-success"
                        style={{ padding: '5px 12px', fontSize: 12 }}
                        onClick={() => addToBill(med)}>
                        + Add
                      </button>
                      <button className="btn btn-secondary"
                        style={{ padding: '5px 12px', fontSize: 12 }}
                        onClick={() => removeSuggestion(med.id)}>
                        Skip
                      </button>
                    </div>
                  </div>
                ))}
                <button
                  onClick={() => setSuggestions([])}
                  style={{
                    width: '100%', marginTop: 4, padding: '6px',
                    background: 'none', border: '1px dashed #cbd5e1',
                    borderRadius: 8, fontSize: 12, color: '#94a3b8', cursor: 'pointer'
                  }}>
                  Clear all suggestions
                </button>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

export default Scan;