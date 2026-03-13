# Quick Start: Enhanced Ticket Purchase System

## 🚀 Ready to Use!

Your enhanced ticket purchase system is fully implemented and ready. Here's how to start using it right away.

## Step 1: Update Event Detail Page (2 minutes)

Find your event detail template (likely `templates/events/event_detail.html` or similar) and update the purchase button:

### Before:
```django
<a href="{% url 'registration:register_for_event' event.id %}">
    Register Now
</a>
```

### After:
```django
<a href="{% url 'registration:enhanced_purchase' event.id %}" 
   class="bg-indigo-600 text-white px-8 py-3 rounded-lg font-bold hover:bg-indigo-700">
    Purchase Tickets
</a>
```

## Step 2: Add Custom Questions (Optional, 3 minutes)

1. Go to Django Admin: `http://localhost:8000/admin/`
2. Navigate to **Registration** → **Registration Fields**
3. Click **Add Registration Field**
4. Fill in:
   - **Event:** Select your event
   - **Field Name:** `company_name` (lowercase, no spaces)
   - **Field Type:** Text Input
   - **Label:** Company Name
   - **Required:** ✓ (check if required)
   - **Order:** 1
5. Click **Save**

### Example Custom Questions:

**Company Name:**
- Field Name: `company_name`
- Field Type: Text Input
- Label: Company Name
- Required: Yes

**Dietary Preference:**
- Field Name: `dietary_preference`
- Field Type: Dropdown
- Label: Dietary Preference
- Options: `None, Vegetarian, Vegan, Gluten-Free, Halal, Kosher`
- Required: No

**T-Shirt Size:**
- Field Name: `tshirt_size`
- Field Type: Dropdown
- Label: T-Shirt Size
- Options: `XS, S, M, L, XL, XXL`
- Required: Yes

## Step 3: Test the Flow (5 minutes)

1. **Start the server:**
   ```bash
   python manage.py runserver
   ```

2. **Log in as a participant**

3. **Navigate to an event**

4. **Click "Purchase Tickets"**

5. **Test the 4-step flow:**
   - **Step 1:** Select 2-3 tickets
   - **Step 2:** Notice first ticket is auto-filled with your info
   - **Step 3:** Try the "Use same info" checkbox
   - **Step 4:** Answer custom questions
   - **Step 5:** Review and complete purchase

6. **View your purchase:**
   - Go to "My Purchases"
   - Click on the purchase to see details
   - View QR codes for each ticket

## Step 4: View Purchase Data (2 minutes)

1. Go to Django Admin
2. Navigate to **Registration** → **Ticket Purchases**
3. Click on a purchase to see:
   - Buyer information
   - All tickets
   - Attendee details
   - Custom question answers

## 🎯 Key URLs

| Page | URL |
|------|-----|
| Purchase Tickets | `/registration/purchase/<event_id>/` |
| My Purchases | `/registration/my-purchases/` |
| Purchase Detail | `/registration/purchase/<id>/detail/` |
| Success Page | `/registration/purchase-success/<id>/` |

## 💡 Quick Tips

### For Participants:
- **Auto-fill works only when logged in** - Make sure users are authenticated
- **Edit any field** - All auto-filled data can be changed
- **Use checkbox** - "Use same info for all tickets" saves time
- **Print tickets** - Use the print button on purchase detail page

### For Organizers:
- **Add questions early** - Create custom fields before event goes live
- **Test thoroughly** - Purchase test tickets to verify flow
- **Export data** - Use Django admin to export attendee information
- **Check answers** - View custom question responses in Ticket Answers

### For Developers:
- **Old system still works** - Original registration is untouched
- **API available** - Use `/api/user-info/` and `/api/validate-promo/`
- **Extend easily** - Add new fields to models as needed
- **Customize UI** - Templates use Tailwind CSS for easy styling

## 🔧 Troubleshooting

### Issue: Auto-fill not working
**Solution:** Ensure user is logged in. Check that user has `first_name`, `last_name`, and `email` in their profile.

### Issue: Custom questions not showing
**Solution:** 
1. Check that questions are created for the correct event
2. Verify `is_active` is checked
3. Ensure questions have proper `order` values

### Issue: Purchase fails
**Solution:**
1. Check that ticket types are available
2. Verify event is published and active
3. Check browser console for JavaScript errors

### Issue: QR codes not displaying
**Solution:** Ensure `qrcode` Python package is installed:
```bash
pip install qrcode[pil]
```

## 📊 What You Get

### Buyer Experience:
1. Fast checkout with auto-fill
2. Buy tickets for multiple people
3. Answer custom questions
4. Apply promo codes
5. View purchase history
6. Print tickets with QR codes

### Organizer Benefits:
1. Collect custom data per ticket
2. Track buyer vs attendee
3. Export attendee information
4. View all purchases in admin
5. Manage ticket inventory
6. Apply promo codes

## 🎉 You're Done!

The enhanced ticket purchase system is now active. Your participants can:
- ✅ Purchase multiple tickets in one transaction
- ✅ Buy tickets for friends and family
- ✅ Enjoy fast checkout with auto-fill
- ✅ Answer your custom questions
- ✅ View their purchase history
- ✅ Access QR codes for check-in

## 📚 More Information

- **Full Guide:** See `ENHANCED_TICKET_PURCHASE_GUIDE.md`
- **Summary:** See `TICKET_PURCHASE_SUMMARY.md`
- **Checklist:** See `IMPLEMENTATION_CHECKLIST.md`

## 🆘 Need Help?

1. Check the documentation files
2. Review Django admin for data
3. Check server logs for errors
4. Verify migrations are applied: `python manage.py migrate`

---

**Status:** ✅ Ready for Production

Start using your professional ticket purchase system now!
