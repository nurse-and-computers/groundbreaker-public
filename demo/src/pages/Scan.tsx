import { useState } from 'react';
import type { DragEvent } from 'react';

const Scan: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) setFile(e.target.files[0]);
  };

  const handleUpload = () => {
    if (!file) return;
    console.log('Uploading file:', file.name);
    // TODO: connect backend API here
  };

  const handleDrag = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    if (e.type === 'dragleave') setDragActive(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]);
  };

  // Inline styles
  const pageStyle: React.CSSProperties = {
    backgroundColor: '#FAF9F6',
    minHeight: '100vh',
    paddingTop: '80px', // leaves space for navbar
    display: 'flex',
    justifyContent: 'center',
  };

  const cardStyle: React.CSSProperties = {
    backgroundColor: '#fff',
    padding: '2rem',
    borderRadius: '1rem',
    boxShadow: '0 6px 20px rgba(0, 0, 0, 0.08)',
    width: '100%',
    maxWidth: '400px',
    textAlign: 'center',
    height: '300px'
  };

  const dropzoneStyle: React.CSSProperties = {
    border: `2px dashed ${dragActive ? '#2563eb' : '#ddd'}`,
    borderRadius: '0.75rem',
    padding: '2rem',
    cursor: 'pointer',
    marginBottom: '1.5rem',
    color: dragActive ? '#2563eb' : '#555',
    transition: 'border-color 0.2s, color 0.2s',
  };

  const hiddenInputStyle: React.CSSProperties = {
    display: 'none',
  };

  const uploadBtnStyle: React.CSSProperties = {
    padding: '0.75rem 1.5rem',
    borderRadius: '0.5rem',
    border: 'none',
    backgroundColor: file ? '#2563eb' : '#ccc',
    color: '#fff',
    fontWeight: 600,
    cursor: file ? 'pointer' : 'not-allowed',
  };

  const titleStyle: React.CSSProperties = {
    marginBottom: '1.5rem',
    fontSize: '1.5rem',
    fontWeight: 700,
    color: '#2563eb',
  };

  const fileTextStyle: React.CSSProperties = {
    fontSize: '0.9rem',
    color: '#555',
  };

  return (
    <div style={pageStyle}>
      <div style={cardStyle}>
        <h1 style={titleStyle}>Upload Home Scan</h1>

        <div
          style={dropzoneStyle}
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-upload')?.click()}
        >
          {file ? (
            <p style={fileTextStyle}>{file.name}</p>
          ) : (
            <p style={fileTextStyle}>Drag & drop your video here, or click to select</p>
          )}
          <input
            id="file-upload"
            type="file"
            accept="video/*"
            onChange={handleFileChange}
            style={hiddenInputStyle}
          />
        </div>

        <button style={uploadBtnStyle} onClick={handleUpload} disabled={!file}>
          Upload
        </button>

        {file && <p style={{ ...fileTextStyle, marginTop: '1rem' }}>Selected file: {file.name}</p>}
      </div>
    </div>
  );
};

export default Scan;
