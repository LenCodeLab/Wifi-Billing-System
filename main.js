document.querySelectorAll('.buy-btn').forEach(btn => {
  btn.addEventListener('click', async function(e) {
    const packageDiv = btn.closest('.package');
    const packageType = packageDiv.getAttribute('data-package');
    const phone = document.getElementById('phone').value.trim();
    const statusDiv = document.getElementById('status');
    statusDiv.textContent = '';

    if (!phone.match(/^07\d{8}$/)) {
      statusDiv.textContent = 'Please enter a valid Kenyan phone number (e.g., 0712345678)';
      return;
    }

    // Optionally, you may want to auto-detect MAC (advanced, usually passed from backend)
    // For now, just send phone and package type
    btn.disabled = true;
    btn.textContent = 'Processing...';

    try {
      const response = await fetch('/api/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: phone,
          package: packageType
          // Add mac_address if available
        })
      });

      const data = await response.json();
      if (data.success) {
        statusDiv.textContent = 
          'STK Push sent to your phone. Complete payment to activate your internet package.';
      } else {
        statusDiv.textContent = data.message || 'Sorry, something went wrong.';
      }
    } catch (err) {
      statusDiv.textContent = 'Network error. Please try again.';
    } finally {
      btn.disabled = false;
      btn.textContent = 'Buy Now';
    }
  });
});