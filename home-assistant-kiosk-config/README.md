# Home Assistant Kiosk Configuration for "namo" User

**Target System:** http://192.168.0.97:8123/  
**Target User:** namo  
**Date Created:** 2026-09-11  

## Overview

This package contains configuration files and instructions to enable kiosk mode for the "namo" user in Home Assistant. When this user logs in, they will only see the dashboard content without the sidebar, header, or additional menus.

## What's Included

1. **namo-kiosk.js** - Custom JavaScript solution for hiding UI elements
2. **configuration-yaml-additions.yaml** - Configuration.yaml modifications needed
3. **dashboard-config.yaml** - Example dashboard configuration template
4. **INSTALLATION-INSTRUCTIONS.md** - Detailed step-by-step installation guide
5. **ALTERNATIVE-HACS-KIOSK-MODE.md** - Guide for using HACS Kiosk Mode integration

## Quick Start

### Option 1: Custom JavaScript (Lightweight)

1. Copy `namo-kiosk.js` to `/config/www/namo-kiosk.js` on your HA server
2. Add to `/config/configuration.yaml`:
   ```yaml
   frontend:
     extra_module_url:
       - /local/namo-kiosk.js?v=4
   ```
3. Restart Home Assistant
4. Test by logging in as "namo" user

**Full instructions:** See `INSTALLATION-INSTRUCTIONS.md`

### Option 2: HACS Kiosk Mode (Recommended)

1. Install "Kiosk Mode" from HACS → Frontend
2. Add to your dashboard raw configuration:
   ```yaml
   kiosk_mode:
     users:
       - namo
     hide_header: true
     hide_sidebar: true
     hide_overflow: true
   ```
3. Test by logging in as "namo" user

**Full instructions:** See `ALTERNATIVE-HACS-KIOSK-MODE.md`

## Which Option to Choose?

| Aspect | Custom JS | HACS Kiosk Mode |
|--------|-----------|-----------------|
| Complexity | Simple | Moderate |
| Maintenance | Manual | Automatic updates |
| Features | Basic | Advanced |
| **Best for** | Quick setup | Production use |

**Recommendation:** If HACS is installed or can be installed, use **Option 2 (HACS Kiosk Mode)**.

## Prerequisites

- Home Assistant running at http://192.168.0.97:8123/
- User "namo" already created (username: "namo")
- Admin access to modify configuration files
- (For Option 2) HACS installed

## Testing Checklist

After installation:

- [ ] Log out from current session
- [ ] Open incognito/private browser window
- [ ] Navigate to http://192.168.0.97:8123/
- [ ] Log in as "namo" user
- [ ] Verify: No left sidebar visible
- [ ] Verify: No top header/toolbar visible
- [ ] Verify: Only dashboard content visible
- [ ] Log in as admin in regular window
- [ ] Verify: Admin sees normal interface with sidebar and header

## Troubleshooting

If kiosk mode doesn't work:

1. Check browser console (F12) for errors
2. Verify username is exactly "namo"
3. Clear browser cache
4. Restart Home Assistant
5. See detailed troubleshooting in respective instruction files

## Network Access Limitation

**Important:** The HA server at 192.168.0.97 is on a local network and was not accessible from the cloud agent environment where this configuration was prepared. Therefore:

- ✅ Configuration files have been created and tested for syntax
- ✅ Instructions are complete and comprehensive
- ❌ Live testing on the actual HA instance was not possible
- ❌ Current installation status could not be verified

**Action Required:** These files need to be manually uploaded to the HA server and tested.

## File Transfer Methods

To transfer these files to your HA server:

1. **Samba/SMB Share** (if configured)
   - Connect to `\\192.168.0.97\config`
   - Copy files to appropriate locations

2. **File Editor Add-on**
   - Install "File Editor" from Add-on Store
   - Create/edit files through the web interface

3. **SSH/Terminal** (if SSH add-on installed)
   - `scp` files to the server
   - Or use `nano`/`vi` to create them directly

4. **Studio Code Server Add-on**
   - Install "Studio Code Server" add-on
   - Edit files through VS Code interface

## Support

For issues:
- Check Home Assistant logs: Settings → System → Logs
- Review browser console (F12) for JavaScript errors
- Consult Home Assistant community forums
- Check HACS Kiosk Mode GitHub issues (if using that option)

## Version

- Custom Script Version: v4
- HACS Kiosk Mode: Latest available via HACS
- Created: 2026-09-11
- HA Instance: http://192.168.0.97:8123/

---

**Next Step:** Read `INSTALLATION-INSTRUCTIONS.md` or `ALTERNATIVE-HACS-KIOSK-MODE.md` for detailed setup.
