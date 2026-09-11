# Home Assistant Kiosk Mode Configuration for "namo" User

## Goal
When logged in with the "namo" account, the user should only see the home control dashboard without:
- Left sidebar menu
- Top header bar
- Any additional menus

## Files Included

1. **namo-kiosk.js** - Custom JavaScript to hide UI elements for "namo" user
2. **configuration-yaml-additions.yaml** - Required configuration.yaml changes
3. **dashboard-config.yaml** - Example dashboard configuration

## Installation Steps

### Step 1: Upload the Kiosk Script

1. Access your Home Assistant server (via SSH, Samba, File Editor add-on, etc.)
2. Navigate to `/config/www/` directory
   - If `www` folder doesn't exist, create it: `mkdir -p /config/www`
3. Copy `namo-kiosk.js` to `/config/www/namo-kiosk.js`

### Step 2: Modify configuration.yaml

1. Open `/config/configuration.yaml`
2. Find the `frontend:` section (or add it if it doesn't exist)
3. Add or modify to include:

```yaml
frontend:
  extra_module_url:
    - /local/namo-kiosk.js?v=4
```

**Note:** If you already have `extra_module_url` entries, add this as another list item.

### Step 3: Verify User "namo" Exists

1. Go to Settings → People → Users
2. Make sure user "namo" exists with:
   - **Username:** namo
   - **Name:** Namo (or "namo" - the script checks case-insensitively)
   - **Type:** Local user
   - **Can only login from local network:** Recommended for security

### Step 4: Restart Home Assistant

1. Go to Developer Tools → YAML → Check Configuration
2. If no errors, click "Restart" at the top right
3. Confirm the restart

### Step 5: Test the Configuration

1. Open a **new private/incognito browser window**
2. Navigate to `http://192.168.0.97:8123/`
3. Log in with user "namo" and its password
4. You should see:
   - ✅ Only the dashboard content
   - ❌ No left sidebar
   - ❌ No top header bar

5. To verify admin access is unaffected, log out and log in with an admin account in a regular browser window

## Troubleshooting

### Kiosk mode not activating

1. Open browser console (F12) when logged in as "namo"
2. Look for messages starting with "Loading namo-kiosk.js"
3. Check what user name is detected

### Script not loading

1. Verify file exists at `/config/www/namo-kiosk.js`
2. Check `configuration.yaml` has the correct `frontend:` section
3. Try incrementing version: `/local/namo-kiosk.js?v=5`
4. Restart Home Assistant
5. Clear browser cache (Ctrl+Shift+Delete)

### Sidebar/header still visible

1. The script uses Home Assistant's shadow DOM structure
2. If HA version changed significantly, the selectors might need updating
3. Check browser console for any errors
4. Consider installing HACS Kiosk Mode as alternative (see below)

## Alternative: HACS Kiosk Mode Integration

If the custom script doesn't work perfectly, you can use the HACS Kiosk Mode integration:

### Install HACS Kiosk Mode:

1. Go to HACS → Frontend
2. Click "+ Explore & Download Repositories"
3. Search for "Kiosk Mode"
4. Click "Download"
5. Restart Home Assistant

### Configure Kiosk Mode:

1. In your dashboard, click the three dots (⋮) → "Edit Dashboard"
2. Click the three dots again → "Raw configuration editor"
3. At the top level (same level as `views:`), add:

```yaml
kiosk_mode:
  users:
    - namo
  hide_header: true
  hide_sidebar: true
  hide_overflow: true
```

4. Save and reload the page

## Security Notes

- The "namo" user should have a strong password
- Consider restricting to local network only
- Dashboard permissions can be further restricted via Home Assistant's user management
- For public kiosks, consider setting up auto-login with kiosk browser extensions

## Version History

- v4 (2026-09-11): Enhanced shadow DOM traversal, added periodic reapplication
- v3 (Previous): Initial version with basic hiding

## Support

If issues persist, check:
- Home Assistant version compatibility
- Browser compatibility (Chrome/Edge recommended)
- System logs: Settings → System → Logs

---

**Created:** 2026-09-11
**For HA Instance:** http://192.168.0.97:8123/
**Target User:** namo
