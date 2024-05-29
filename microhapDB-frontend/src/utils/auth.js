// src/utils/auth.js
export async function fetchProtectedData() {
    const token = localStorage.getItem('access_token');
    if (!token) {
      throw new Error('No access token found');
    }
  
    const response = await fetch('https://myfastapiapp.loca.lt/auth/users/me', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
  
    if (!response.ok) {
      throw new Error('Failed to fetch protected data');
    }
  
    return response.json();
  }
  