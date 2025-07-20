// MongoDB initialization script for Vidzilla

// Switch to the vidzilla database
db = db.getSiblingDB('vidzilla');

// Create collections with validation
db.createCollection('users', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['user_id', 'downloads_count'],
      properties: {
        user_id: {
          bsonType: 'long',
          description: 'Telegram user ID - required'
        },
        username: {
          bsonType: ['string', 'null'],
          description: 'Telegram username - optional'
        },
        downloads_count: {
          bsonType: 'int',
          minimum: 0,
          description: 'Number of downloads - required'
        },
        subscription_end: {
          bsonType: ['date', 'null'],
          description: 'Subscription end date - optional'
        },
        language: {
          bsonType: ['string', 'null'],
          description: 'User language code - optional'
        },
        created_at: {
          bsonType: 'date',
          description: 'Account creation date'
        },
        last_active: {
          bsonType: 'date',
          description: 'Last activity date'
        }
      }
    }
  }
});

db.createCollection('coupons', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['code', 'duration', 'used', 'created_at'],
      properties: {
        code: {
          bsonType: 'string',
          description: 'Coupon code - required'
        },
        duration: {
          bsonType: 'string',
          enum: ['1month'],
          description: 'Coupon duration - required'
        },
        used: {
          bsonType: 'bool',
          description: 'Whether coupon is used - required'
        },
        used_by: {
          bsonType: ['long', 'null'],
          description: 'User ID who used the coupon - optional'
        },
        used_at: {
          bsonType: ['date', 'null'],
          description: 'When coupon was used - optional'
        },
        created_at: {
          bsonType: 'date',
          description: 'Coupon creation date - required'
        }
      }
    }
  }
});

// Create indexes for better performance
db.users.createIndex({ 'user_id': 1 }, { unique: true });
db.users.createIndex({ 'username': 1 });
db.users.createIndex({ 'subscription_end': 1 });
db.users.createIndex({ 'created_at': 1 });
db.users.createIndex({ 'last_active': 1 });

db.coupons.createIndex({ 'code': 1 }, { unique: true });
db.coupons.createIndex({ 'used': 1 });
db.coupons.createIndex({ 'created_at': 1 });
db.coupons.createIndex({ 'used_by': 1 });

// Insert default admin user (optional)
// db.users.insertOne({
//   user_id: NumberLong(123456789),
//   username: 'admin',
//   downloads_count: 0,
//   subscription_end: null,
//   language: 'en',
//   created_at: new Date(),
//   last_active: new Date()
// });

print('✅ Vidzilla database initialized successfully');
print('📊 Collections created: users, coupons');
print('🔍 Indexes created for optimal performance');
print('🚀 Ready to start the bot!');