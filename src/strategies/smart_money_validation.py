# src/strategies/smart_money_analyzer.py
# Добавляем метод для валидации API ключей

# ... (в конец класса SmartMoneyAnalyzer)

    async def validate_api_keys(self) -> Dict[str, bool]:
        """
        Проверяет валидность API ключей Smart Money.
        Возвращает статус для каждого сервиса.
        """
        status = {
            'coinglass': False,
            'hyblock': False,
            'using_mock_data': True
        }
        
        # Coinglass validation
        if self.coinglass_key and self.coinglass_key != "":
            try:
                await self._ensure_session()
                url = "https://open-api.coinglass.com/public/v2/indicator/funding_usd_history"
                headers = {"coinglassSecret": self.coinglass_key}
                
                async with self.session.get(url, headers=headers, timeout=5) as resp:
                    if resp.status == 200:
                        status['coinglass'] = True
                        status['using_mock_data'] = False
                        logger.info("✅ Coinglass API key validated")
                    else:
                        logger.warning(f"⚠️  Coinglass API key invalid (status: {resp.status})")
            except Exception as e:
                logger.warning(f"⚠️  Coinglass API check failed: {e}")
        
        # Hyblock validation (если есть API)
        if self.hyblock_key and self.hyblock_key != "":
            # TODO: Add Hyblock validation when API is available
            pass
        
        if status['using_mock_data']:
            logger.warning("⚠️  Using MOCK data for Smart Money (no valid API keys)")
            logger.warning("   For production: add COINGLASS_API_KEY to .env")
        
        return status
