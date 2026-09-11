# Alternative Solution: Using HACS Kiosk Mode

If you prefer to use the official HACS Kiosk Mode integration instead of the custom JavaScript:

## Prerequisites

1. HACS (Home Assistant Community Store) must be installed
   - If not installed, visit: https://hacs.xyz/docs/setup/download

## Installation Steps

### 1. Install Kiosk Mode via HACS

1. Open Home Assistant at http://192.168.0.97:8123/
2. Go to **HACS** (in the sidebar)
3. Click on **Frontend** tab
4. Click the **+ Explore & Download Repositories** button (bottom right)
5. Search for **"Kiosk Mode"** (by maykar)
6. Click on it, then click **Download**
7. Click **Download** again to confirm
8. **Restart Home Assistant**: Settings → System → Restart

### 2. Add Kiosk Mode to Your Dashboard

#### Method A: Via Dashboard Raw Config (Recommended)

1. Navigate to your main dashboard (Overview)
2. Click the **⋮** (three dots) in top right → **Edit Dashboard**
3. Click the **⋮** again → **Raw configuration editor**
4. At the very top of the configuration (before or after `title:`), add:

```yaml
kiosk_mode:
  users:
    - namo
  hide_header: true
  hide_sidebar: true
  hide_overflow: true
  hide_account: true
  hide_search: true
```

5. Click **Save**
6. Click **Done** to exit edit mode

#### Method B: Via Lovelace Resources (If Method A doesn't work)

1. Go to **Settings** → **Dashboards** → **Resources** tab
2. Click **+ Add Resource**
3. Enter:
   - **URL:** `/hacsfiles/kiosk-mode/kiosk-mode.js`
   - **Resource type:** JavaScript Module
4. Click **Create**

Then add the kiosk_mode configuration as shown in Method A.

### 3. Test Configuration

1. **Important:** Log out completely from your current session
2. Open a **new private/incognito window**
3. Go to http://192.168.0.97:8123/
4. Log in as user **"namo"**
5. You should see only the dashboard content without:
   - Sidebar
   - Header/toolbar
   - User account menu

### 4. Verify Admin Access Still Works

1. In a regular (non-incognito) browser window
2. Make sure you're logged in as admin
3. Verify that sidebar and header are still visible
4. This confirms kiosk mode only applies to "namo" user

## Advanced Configuration Options

You can customize kiosk mode further:

```yaml
kiosk_mode:
  users:
    - namo
  hide_header: true          # Hide top header bar
  hide_sidebar: true         # Hide left sidebar
  hide_overflow: true        # Hide overflow menu (⋮)
  hide_account: true         # Hide account menu
  hide_search: true          # Hide search button
  ignore_entity_settings: true  # Ignore per-entity settings
  ignore_mobile_settings: true  # Apply on mobile too
```

## Per-Dashboard Configuration

If you want kiosk mode only on specific dashboards:

1. Create a dedicated dashboard for "namo" user
2. Go to that dashboard
3. Edit it and add kiosk_mode config only to that dashboard
4. Set "namo" user's default dashboard to this one

## Troubleshooting

### Kiosk Mode Not Working

1. **Clear browser cache**: Ctrl+Shift+Delete, clear cache and reload
2. **Check HACS installation**: HACS → Frontend → Search "Kiosk Mode" → should show "Installed"
3. **Verify username**: The username must exactly match "namo" (case-insensitive should work)
4. **Check browser console** (F12):
   - Look for "kiosk-mode" messages
   - Check for any JavaScript errors

### Still See Sidebar/Header

1. Make sure you're logged in as "namo", not admin
2. Try logging out completely and logging back in
3. Try different browser or incognito mode
4. Verify the configuration syntax is correct (YAML indentation matters!)

### Admin Account Also Affected

1. Check if admin username is accidentally listed in `users:` array
2. Verify you're logged in with the correct account
3. Clear browser cache and cookies for the site

## Comparison: Custom Script vs HACS Kiosk Mode

| Feature | Custom namo-kiosk.js | HACS Kiosk Mode |
|---------|---------------------|-----------------|
| Installation | Manual file copy | Via HACS interface |
| Maintenance | Manual updates | Auto-updates via HACS |
| Configuration | JavaScript code | YAML config |
| Reliability | Depends on HA structure | Actively maintained |
| Features | Basic hiding | Many options |
| **Recommendation** | Good for quick setup | **Better for production** |

## Final Recommendation

**Use HACS Kiosk Mode** if:
- ✅ HACS is already installed or you can install it
- ✅ You want easy updates and maintenance
- ✅ You need more configuration options
- ✅ You want community support

**Use Custom Script** if:
- ✅ HACS is not available or you can't install it
- ✅ You need a quick, lightweight solution
- ✅ You want to customize the hiding logic yourself

---

**Note:** Both solutions work, but HACS Kiosk Mode is more robust and easier to maintain long-term.
