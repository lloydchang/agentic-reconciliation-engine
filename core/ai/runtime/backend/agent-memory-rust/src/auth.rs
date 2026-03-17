use crate::error::Result;
use jsonwebtoken::{decode, encode, Algorithm, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::time::{SystemTime, UNIX_EPOCH};

/// Authentication service
pub struct AuthService {
    jwt_secret: Option<String>,
    api_keys: HashSet<String>,
    enabled: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,
    pub exp: u64,
    pub iat: u64,
    pub iss: String,
}

impl AuthService {
    pub fn new(jwt_secret: Option<String>, api_keys: Vec<String>, enabled: bool) -> Self {
        Self {
            jwt_secret,
            api_keys: api_keys.into_iter().collect(),
            enabled,
        }
    }

    pub fn validate_api_key(&self, api_key: &str) -> Result<bool> {
        if !self.enabled {
            return Ok(true); // No auth required
        }

        Ok(self.api_keys.contains(api_key))
    }

    pub fn generate_token(&self, subject: &str, expires_in_hours: u64) -> Result<String> {
        if !self.enabled || self.jwt_secret.is_none() {
            return Err(crate::error::Error::Authentication("Authentication disabled".to_string()));
        }

        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map_err(|e| crate::error::Error::Authentication(format!("Time error: {}", e)))?
            .as_secs();

        let claims = Claims {
            sub: subject.to_string(),
            exp: now + (expires_in_hours * 3600),
            iat: now,
            iss: "agent-memory".to_string(),
        };

        let secret = self.jwt_secret.as_ref().unwrap();
        let encoding_key = EncodingKey::from_secret(secret.as_bytes());

        encode(&Header::default(), &claims, &encoding_key)
            .map_err(|e| crate::error::Error::Authentication(format!("Token generation failed: {}", e)))
    }

    pub fn validate_token(&self, token: &str) -> Result<Claims> {
        if !self.enabled || self.jwt_secret.is_none() {
            return Err(crate::error::Error::Authentication("Authentication disabled".to_string()));
        }

        let secret = self.jwt_secret.as_ref().unwrap();
        let decoding_key = DecodingKey::from_secret(secret.as_bytes());
        let validation = Validation::new(Algorithm::HS256);

        let token_data = decode::<Claims>(token, &decoding_key, &validation)
            .map_err(|e| crate::error::Error::Authentication(format!("Token validation failed: {}", e)))?;

        Ok(token_data.claims)
    }

    pub fn extract_token_from_header(&self, auth_header: &str) -> Result<String> {
        if !auth_header.starts_with("Bearer ") {
            return Err(crate::error::Error::Authentication("Invalid authorization header format".to_string()));
        }

        Ok(auth_header[7..].to_string())
    }

    pub fn is_token_expired(&self, claims: &Claims) -> bool {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();

        claims.exp < now
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_api_key_validation() {
        let auth = AuthService::new(
            None,
            vec!["key1".to_string(), "key2".to_string()],
            true,
        );

        assert!(auth.validate_api_key("key1").unwrap());
        assert!(auth.validate_api_key("key2").unwrap());
        assert!(!auth.validate_api_key("invalid").unwrap());

        let auth_disabled = AuthService::new(None, vec![], false);
        assert!(auth_disabled.validate_api_key("any").unwrap());
    }

    #[test]
    fn test_token_generation_and_validation() -> Result<()> {
        let auth = AuthService::new(
            Some("test_secret".to_string()),
            vec![],
            true,
        );

        let token = auth.generate_token("test_user", 1)?;
        let claims = auth.validate_token(&token)?;

        assert_eq!(claims.sub, "test_user");
        assert_eq!(claims.iss, "agent-memory");

        Ok(())
    }

    #[test]
    fn test_token_extraction() {
        let auth = AuthService::new(None, vec![], true);
        
        let valid_header = "Bearer token123";
        assert_eq!(auth.extract_token_from_header(valid_header).unwrap(), "token123");

        let invalid_header = "Basic token123";
        assert!(auth.extract_token_from_header(invalid_header).is_err());
    }
}
