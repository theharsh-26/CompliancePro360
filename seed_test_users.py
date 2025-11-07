"""
Seed Test Users - CompliancePro360
Creates test users for development and testing

Run: python seed_test_users.py
"""

import sys
import asyncio
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from app.core.database import SessionLocal, init_db
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.models.company import Company
from app.models.license import License, LicenseType, LicenseStatus

def create_test_data():
    """Create test users and data"""
    
    print("\n" + "="*70)
    print("  🌱 Seeding Test Users - CompliancePro360")
    print("="*70 + "\n")
    
    # Initialize database
    init_db()
    db = SessionLocal()
    
    try:
        # ============================================
        # 1. Create Test Tenant (CA Firm)
        # ============================================
        print("[1/5] Creating Test Tenant (CA Firm)...")
        
        tenant_id = str(uuid.uuid4())
        tenant = Tenant(
            tenant_id=tenant_id,
            name="Test CA Firm & Associates",
            subdomain="test-ca-firm",
            email="admin@testfirm.com",
            phone="+91 98765 43210",
            is_active=True,
            is_verified=True,
            subscription_tier="professional"
        )
        db.add(tenant)
        db.flush()
        
        print(f"   ✅ Tenant created: {tenant.name}")
        
        # ============================================
        # 2. Create Test License
        # ============================================
        print("\n[2/5] Creating Test License...")
        
        license_key = License.generate_license_key()
        license = License(
            license_key=license_key,
            license_type=LicenseType.PROFESSIONAL,
            status=LicenseStatus.ACTIVE,
            practitioner_name="Admin User",
            practitioner_email="admin@testfirm.com",
            practitioner_phone="+91 98765 43210",
            firm_name="Test CA Firm & Associates",
            valid_from=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=365),
            monthly_fee=5999,
            adhoc_rate_per_company=40,
            max_companies=200,
            max_clients=20,
            companies_count=2,
            clients_count=1,
            shareable_link=License.generate_shareable_link(license_key),
            tenant_id_fk=tenant.id,
            features={
                "ai_automation": True,
                "data_scraping": True,
                "risk_prediction": True,
                "client_portal": True,
                "whatsapp_notifications": False,
                "api_access": False
            }
        )
        db.add(license)
        db.flush()
        
        print(f"   ✅ License created: {license_key}")
        print(f"   📱 Shareable Link: {license.shareable_link}")
        
        # ============================================
        # 3. Create Test Users
        # ============================================
        print("\n[3/5] Creating Test Users...")
        
        # 3a. System Admin User
        admin_user = User(
            email="admin@test.com",
            first_name="Admin",
            last_name="User",
            phone="+91 98765 00001",
            firm_name="Test CA Firm & Associates",
            role=UserRole.SYSTEM_ADMIN,
            tenant_id=tenant_id,
            tenant_id_fk=tenant.id,
            is_active=True,
            is_verified=True
        )
        admin_user.set_password("admin123")
        db.add(admin_user)
        
        print(f"   ✅ Admin User created")
        print(f"      Email: admin@test.com")
        print(f"      Password: admin123")
        print(f"      Role: SYSTEM_ADMIN (Full access)")
        
        # 3b. Tenant Admin / Practitioner User
        practitioner_user = User(
            email="practitioner@test.com",
            first_name="CA",
            last_name="Practitioner",
            phone="+91 98765 00002",
            firm_name="Test CA Firm & Associates",
            role=UserRole.TENANT_ADMIN,
            tenant_id=tenant_id,
            tenant_id_fk=tenant.id,
            is_active=True,
            is_verified=True
        )
        practitioner_user.set_password("practitioner123")
        db.add(practitioner_user)
        
        print(f"\n   ✅ Practitioner User created")
        print(f"      Email: practitioner@test.com")
        print(f"      Password: practitioner123")
        print(f"      Role: TENANT_ADMIN (CA Firm Admin)")
        
        # 3c. Company User (Client)
        company_user = User(
            email="company@test.com",
            first_name="Company",
            last_name="Director",
            phone="+91 98765 00003",
            firm_name="ABC Private Limited",
            role=UserRole.COMPANY_USER,
            tenant_id=tenant_id,
            tenant_id_fk=tenant.id,
            is_active=True,
            is_verified=True
        )
        company_user.set_password("company123")
        db.add(company_user)
        
        print(f"\n   ✅ Company User created")
        print(f"      Email: company@test.com")
        print(f"      Password: company123")
        print(f"      Role: COMPANY_USER (Limited access)")
        
        db.flush()
        
        # ============================================
        # 4. Create Test Companies
        # ============================================
        print("\n[4/5] Creating Test Companies...")
        
        # Company 1
        company1 = Company(
            name="ABC Private Limited",
            cin="U74999MH2020PTC123456",
            company_type="Private Limited",
            industry="Information Technology",
            registered_address="Mumbai, Maharashtra",
            tenant_id=tenant_id,
            tenant_id_fk=tenant.id,
            is_active=True,
            compliance_score=85
        )
        db.add(company1)
        
        print(f"   ✅ Company 1: ABC Private Limited")
        print(f"      CIN: U74999MH2020PTC123456")
        
        # Company 2
        company2 = Company(
            name="XYZ Traders LLP",
            gstin="27AABCX1234F1Z5",
            company_type="LLP",
            industry="Trading",
            registered_address="Delhi, India",
            tenant_id=tenant_id,
            tenant_id_fk=tenant.id,
            is_active=True,
            compliance_score=72
        )
        db.add(company2)
        
        print(f"   ✅ Company 2: XYZ Traders LLP")
        print(f"      GSTIN: 27AABCX1234F1Z5")
        
        # ============================================
        # 5. Commit All Changes
        # ============================================
        print("\n[5/5] Committing to database...")
        db.commit()
        
        print("   ✅ All test data committed successfully!")
        
        # ============================================
        # Summary
        # ============================================
        print("\n" + "="*70)
        print("  ✅ TEST DATA SEEDED SUCCESSFULLY!")
        print("="*70)
        
        print("\n📋 LOGIN CREDENTIALS:")
        print("-" * 70)
        
        print("\n1️⃣  ADMIN USER (Full System Access)")
        print("   Email:    admin@test.com")
        print("   Password: admin123")
        print("   Role:     System Administrator")
        print("   Access:   All features, all data, license management")
        
        print("\n2️⃣  PRACTITIONER USER (CA Firm Admin)")
        print("   Email:    practitioner@test.com")
        print("   Password: practitioner123")
        print("   Role:     Tenant Admin / CA Practitioner")
        print("   Access:   Manage companies, compliance, invite clients")
        
        print("\n3️⃣  COMPANY USER (Client Portal)")
        print("   Email:    company@test.com")
        print("   Password: company123")
        print("   Role:     Company User / Client")
        print("   Access:   View own company compliance only")
        
        print("\n🏢 TEST COMPANIES:")
        print("-" * 70)
        print("   1. ABC Private Limited (CIN: U74999MH2020PTC123456)")
        print("   2. XYZ Traders LLP (GSTIN: 27AABCX1234F1Z5)")
        
        print("\n🔑 TEST LICENSE:")
        print("-" * 70)
        print(f"   License Key: {license_key}")
        print(f"   Plan:        Professional")
        print(f"   Status:      Active")
        print(f"   Valid Until: {license.valid_until.strftime('%Y-%m-%d')}")
        
        print("\n🌐 ACCESS URLS:")
        print("-" * 70)
        print("   Login Page:  http://localhost:5000/login")
        print("   Dashboard:   http://localhost:5000/dashboard")
        print("   My License:  http://localhost:5000/my-license")
        
        print("\n" + "="*70)
        print("  🚀 Ready to test! Login with any of the above credentials")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    try:
        create_test_data()
    except KeyboardInterrupt:
        print("\n\n⚠️  Seeding cancelled by user")
        sys.exit(0)
