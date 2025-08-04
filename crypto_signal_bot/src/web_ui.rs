use crate::config::Config;

pub struct WebUIController {
    config: Config,
}

impl WebUIController {
    pub fn new(config: Config) -> Self {
        Self { config }
    }

    pub async fn start(&self, port: u16) -> Result<(), Box<dyn std::error::Error>> {
        // Web UI start logic here
        println!("🌐 Web UI started on port {}", port);
        Ok(())
    }
} 