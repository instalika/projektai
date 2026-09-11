// Kiosk Mode configuration for "namo" user
// Place this file in: /config/www/namo-kiosk.js

console.log("Loading namo-kiosk.js v4");

function applyKioskMode() {
  const username = (window.localStorage.getItem('selectedLanguage') || '').toLowerCase();
  const hassUser = (window.hassUser || {}).name || '';
  
  console.log("Checking user:", hassUser);
  
  // Check if current user is "namo"
  if (hassUser.toLowerCase() === 'namo') {
    console.log("Applying kiosk mode for namo user");
    
    // Hide sidebar
    const sidebar = document.querySelector('home-assistant')?.shadowRoot?.querySelector('home-assistant-main')?.shadowRoot?.querySelector('ha-drawer')?.shadowRoot?.querySelector('.mdc-drawer');
    if (sidebar) {
      sidebar.style.display = 'none';
      console.log("Sidebar hidden");
    }
    
    // Hide header
    const header = document.querySelector('home-assistant')?.shadowRoot?.querySelector('home-assistant-main')?.shadowRoot?.querySelector('app-toolbar');
    if (header) {
      header.style.display = 'none';
      console.log("Header hidden");
    }
    
    // Alternative header hiding
    const partialPanelResolver = document.querySelector('home-assistant')?.shadowRoot?.querySelector('home-assistant-main')?.shadowRoot?.querySelector('partial-panel-resolver');
    if (partialPanelResolver) {
      const haPanel = partialPanelResolver.shadowRoot?.querySelector('ha-panel-lovelace');
      if (haPanel) {
        const huiRoot = haPanel.shadowRoot?.querySelector('hui-root');
        if (huiRoot) {
          const appHeader = huiRoot.shadowRoot?.querySelector('app-header');
          if (appHeader) {
            appHeader.style.display = 'none';
            console.log("App header hidden via hui-root");
          }
        }
      }
    }
    
    // Force fullscreen dashboard
    const main = document.querySelector('home-assistant')?.shadowRoot?.querySelector('home-assistant-main');
    if (main) {
      main.style.setProperty('--header-height', '0px');
    }
    
    console.log("Kiosk mode applied successfully");
  } else {
    console.log("User is not 'namo', kiosk mode not applied");
  }
}

// Wait for Home Assistant to load
function waitForHass() {
  if (window.hassUser) {
    console.log("Home Assistant loaded, applying kiosk mode");
    setTimeout(applyKioskMode, 500);
    // Reapply periodically in case of dynamic updates
    setInterval(applyKioskMode, 2000);
  } else {
    console.log("Waiting for Home Assistant to load...");
    setTimeout(waitForHass, 500);
  }
}

// Start when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', waitForHass);
} else {
  waitForHass();
}
