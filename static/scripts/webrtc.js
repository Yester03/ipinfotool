// webrtc.js
// WebRTC leak test implementation.

/**
 * Determine whether an IP address is private.  Covers IPv4 RFC1918 ranges and
 * common IPv6 local prefixes.
 * @param {string} ip
 */
function isPrivateIP(ip) {
  return (
    ip.startsWith('10.') ||
    ip.startsWith('192.168.') ||
    /^172\.(1[6-9]|2\d|3[0-1])\./.test(ip) ||
    ip.startsWith('169.254.') ||
    ip.startsWith('fc00:') ||
    ip.startsWith('fe80:')
  );
}

/**
 * Run the WebRTC leak test.
 */
async function runWebRTCTest() {
  const resultDiv = document.getElementById('webrtc-results');
  const noteDiv = document.getElementById('webrtc-note');
  resultDiv.innerHTML = '';
  noteDiv.textContent = '';
  const publicIPs = new Set();
  const localIPs = new Set();
  // STUN servers to probe.  Additional servers can be added here.
  const iceServers = [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
    { urls: 'stun:stun.cloudflare.com:3478' },
  ];
  const pc = new RTCPeerConnection({ iceServers });
  // Create a data channel to ensure ICE gathering starts
  pc.createDataChannel('dummy');
  pc.onicecandidate = (event) => {
    if (!event.candidate || !event.candidate.candidate) return;
    const parts = event.candidate.candidate.split(' ');
    const ip = parts[4];
    if (!ip) return;
    if (isPrivateIP(ip)) {
      localIPs.add(ip);
    } else {
      publicIPs.add(ip);
    }
  };
  await pc.createOffer().then((offer) => pc.setLocalDescription(offer));
  // Wait for ICE gathering to complete or time out after 3s
  await new Promise((resolve) => {
    let settled = false;
    const finish = () => {
      if (!settled) {
        settled = true;
        resolve();
      }
    };
    pc.onicegatheringstatechange = () => {
      if (pc.iceGatheringState === 'complete') finish();
    };
    setTimeout(finish, 3000);
  });
  pc.close();
  // Display results
  const list = document.createElement('ul');
  if (publicIPs.size > 0) {
    const li = document.createElement('li');
    li.innerHTML = `<strong>Public IPs:</strong> ${Array.from(publicIPs).join(', ')}`;
    list.appendChild(li);
  }
  if (localIPs.size > 0) {
    const li = document.createElement('li');
    li.innerHTML = `<strong>Private/Internal IPs:</strong> ${Array.from(localIPs).join(', ')}`;
    list.appendChild(li);
  }
  if (list.childElementCount === 0) {
    list.textContent = 'No ICE candidates found.  Your browser may block host candidates.';
  }
  resultDiv.appendChild(list);
  // Provide an explanatory note
  if (localIPs.size > 0) {
    noteDiv.textContent =
      'Your private/internal IP addresses were exposed via WebRTC.  Some VPNs disable host candidates or block WebRTC to prevent this leak.';
  } else {
    noteDiv.textContent =
      'No private IPs were exposed.  Modern browsers often restrict host candidates by default, but results may vary by configuration.';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('start-btn');
  btn.addEventListener('click', () => {
    btn.disabled = true;
    runWebRTCTest().finally(() => {
      btn.disabled = false;
    });
  });
});
