from django.db import models

class Invoice(models.Model):
    invoice_number = models.CharField(max_length=100, verbose_name="Invoice Number")
    vendor_details = models.TextField(verbose_name="Vendor Details")
    date = models.CharField(max_length=20, null=True, blank=True, verbose_name="Invoice Date")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Amount")
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tax Amount")
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Subtotal Amount")
    line_items = models.JSONField(default=dict, verbose_name="Line Items")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.vendor_details}"
 
class InvoiceData(models.Model):
    file_name = models.CharField(max_length=255)
    file_path = models.TextField()
    extracted_data = models.TextField()  # Changed to TextField to handle any string format
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.file_name