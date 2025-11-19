from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from authentication.models import User
from superadmin.models import Business
from reports.views import quick_report
from io import StringIO
import csv
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send daily report via email for all accounts"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            help="Email address to send the report to",
            required=False,
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force send email even if not scheduled time",
            required=False,
        )

    def handle(self, *args, **options):
        # Check if it's 11 PM or force flag is set
        current_time = timezone.now()
        is_scheduled_time = (
            current_time.hour == 23 and current_time.minute == 0
        )  # 11 PM
        force_send = options.get("force", False)

        if not is_scheduled_time and not force_send:
            self.stdout.write(
                self.style.WARNING(
                    f'Not scheduled time. Current time: {current_time.strftime("%H:%M")}. '
                    "Use --force to send immediately."
                )
            )
            return

        # Get email address
        email_address = options.get("email") or "emmychris915@gmail.com"

        try:
            # Generate daily report data for all businesses
            all_reports_data = self.generate_all_business_reports()

            # Send email with all reports
            self.send_report_email(email_address, all_reports_data)

            self.stdout.write(
                self.style.SUCCESS(
                    f'Daily reports for all accounts successfully sent to {email_address} at {current_time.strftime("%Y-%m-%d %H:%M")}'
                )
            )

        except Exception as e:
            logger.error(f"Failed to send daily reports: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f"Failed to send daily reports: {str(e)}")
            )

    def generate_all_business_reports(self):
        """Generate daily report data for all businesses"""
        from datetime import date
        from reports.views import get_date_ranges

        # Get today's date range
        date_ranges = get_date_ranges()
        start_date = date_ranges["daily"]["start"]
        end_date = date_ranges["daily"]["end"]

        # Get all businesses
        businesses = Business.objects.all()
        if not businesses:
            raise Exception("No businesses found")

        all_reports = []

        # Generate report for each business
        for business in businesses:
            try:
                # Get sales data for this business
                from sales.models import Sale
                from django.db.models import Sum, DecimalField
                from decimal import Decimal

                sales = Sale.objects.filter(business=business).filter(
                    sale_date__date__gte=start_date, sale_date__date__lte=end_date
                )

                total_sales = sales.aggregate(total=Sum("total_amount"))[
                    "total"
                ] or Decimal("0")
                total_orders = sales.count()

                # Get expenses data for this business
                from expenses.models import Expense

                expenses = Expense.objects.filter(business=business).filter(
                    date__gte=start_date, date__lte=end_date
                )
                total_expenses = expenses.aggregate(total=Sum("amount"))[
                    "total"
                ] or Decimal("0")

                # Calculate profit
                estimated_cogs = total_sales * Decimal("0.6")
                gross_profit = total_sales - estimated_cogs
                net_profit = gross_profit - total_expenses

                # Get top selling products for this business
                from sales.models import SaleItem

                top_products = (
                    SaleItem.objects.filter(sale__business=business)
                    .filter(
                        sale__sale_date__date__gte=start_date,
                        sale__sale_date__date__lte=end_date,
                    )
                    .values("product__name")
                    .annotate(
                        total_sold=Sum("quantity"), total_revenue=Sum("total_price")
                    )
                    .order_by("-total_sold")[:5]
                )

                # Generate recommendations
                from reports.views import generate_recommendations

                recommendations = generate_recommendations(
                    "daily",
                    float(total_sales),
                    total_orders,
                    float(total_expenses),
                    float(net_profit),
                    top_products,
                )

                all_reports.append(
                    {
                        "business": business,
                        "start_date": start_date,
                        "end_date": end_date,
                        "total_sales": float(total_sales),
                        "total_orders": total_orders,
                        "total_expenses": float(total_expenses),
                        "gross_profit": float(gross_profit),
                        "net_profit": float(net_profit),
                        "top_products": top_products,
                        "recommendations": recommendations,
                    }
                )
            except Exception as e:
                logger.error(
                    f"Failed to generate report for business {business.company_name}: {str(e)}"
                )
                self.stdout.write(
                    self.style.WARNING(
                        f"Failed to generate report for business {business.company_name}: {str(e)}"
                    )
                )

        return all_reports

    def create_csv_attachment(self, all_reports_data):
        """Create CSV attachment for all reports"""
        from io import StringIO
        import csv

        # Create CSV content
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)

        # Write header
        writer.writerow(["Daily Business Reports for All Accounts"])
        writer.writerow(
            [
                "Report Date:",
                all_reports_data[0]["start_date"] if all_reports_data else "N/A",
            ]
        )
        writer.writerow([])

        # Write report for each business
        for report_data in all_reports_data:
            writer.writerow([f"Business: {report_data['business'].company_name}"])
            writer.writerow([])

            # Write summary data
            writer.writerow(["Summary"])
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Total Sales", f"${report_data['total_sales']:.2f}"])
            writer.writerow(["Total Orders", report_data["total_orders"]])
            writer.writerow(["Total Expenses", f"${report_data['total_expenses']:.2f}"])
            writer.writerow(["Net Profit", f"${report_data['net_profit']:.2f}"])
            writer.writerow([])

            # Write top selling products
            writer.writerow(["Top Selling Products"])
            writer.writerow(["Product", "Quantity Sold", "Revenue"])
            for product in report_data["top_products"]:
                writer.writerow(
                    [
                        product["product__name"],
                        product["total_sold"],
                        f"${product['total_revenue']:.2f}",
                    ]
                )
            writer.writerow([])

            # Write recommendations
            writer.writerow(["Business Recommendations"])
            writer.writerow(
                ["Priority", "Category", "Title", "Description", "Suggested Action"]
            )
            for rec in report_data["recommendations"]:
                priority = rec.get("priority", "medium")
                priority_label = {
                    "high": "HIGH",
                    "medium": "MEDIUM",
                    "low": "LOW",
                    "positive": "POSITIVE",
                }.get(priority, "MEDIUM")

                writer.writerow(
                    [
                        priority_label,
                        rec.get("type", "general").title(),
                        rec.get("title", ""),
                        rec.get("description", ""),
                        rec.get("action", ""),
                    ]
                )
            writer.writerow([])
            writer.writerow(["=" * 50])
            writer.writerow([])

        return csv_buffer.getvalue()

    def send_report_email(self, email_address, all_reports_data):
        """Send the reports via email"""
        # Create email subject
        subject = f"Daily Business Reports - All Accounts - {all_reports_data[0]['start_date'] if all_reports_data else 'N/A'}"

        # Create email body (HTML)
        html_content = render_to_string(
            "reports/email_all_daily_reports.html",
            {
                "reports": all_reports_data,
                "report_date": (
                    all_reports_data[0]["start_date"] if all_reports_data else "N/A"
                ),
            },
        )

        # Create plain text version
        text_content = f"""
Daily Business Reports for All Accounts
Report Date: {all_reports_data[0]['start_date'] if all_reports_data else 'N/A'}

"""
        for report_data in all_reports_data:
            text_content += f"""
Business: {report_data['business'].company_name}
- Total Sales: ${report_data['total_sales']:.2f}
- Total Orders: {report_data['total_orders']}
- Total Expenses: ${report_data['total_expenses']:.2f}
- Net Profit: ${report_data['net_profit']:.2f}

Top Selling Products:
"""
            for product in report_data["top_products"]:
                text_content += f"- {product['product__name']}: {product['total_sold']} units, ${product['total_revenue']:.2f}\n"

            text_content += "\nRecommendations:\n"
            for rec in report_data["recommendations"]:
                text_content += (
                    f"- {rec.get('title', '')}: {rec.get('description', '')}\n"
                )
            text_content += "\n" + "=" * 50 + "\n"

        # Create email
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email_address],
        )
        email.content_subtype = "html"  # Main content is HTML

        # Add CSV attachment
        csv_content = self.create_csv_attachment(all_reports_data)
        email.attach(
            f"daily_reports_all_accounts_{all_reports_data[0]['start_date'] if all_reports_data else 'N/A'}.csv",
            csv_content,
            "text/csv",
        )

        # Send email
        email.send()
