import json

# Qlib：https://github.com/microsoft/qlib


class AlphaFactorGenerator:
    def get_alpha_expression(self):
        fields = []
        for i in range(59, 0, -1):
            fields += ["shift(close, %d)/close" % i]
        fields += ["close/close"]
        for i in range(59, 0, -1):
            fields += ["shift(open, %d)/close" % i]
        fields += ["open/close"]
        for i in range(59, 0, -1):
            fields += ["shift(high, %d)/close" % i]
        fields += ["high/close"]
        for i in range(59, 0, -1):
            fields += ["shift(low, %d)/close" % i]
        fields += ["low/close"]
        for i in range(59, 0, -1):
            fields += ["shift(vwap, %d)/close" % i]
        fields += ["vwap/close"]
        for i in range(59, 0, -1):
            fields += ["shift(volume, %d)/(volume+1e-12)" % i]
        fields += ["volume/(volume+1e-12)"]
        result = {}
        for index, field_expression in enumerate(fields, start=1):
            result[f"alpha_{len(fields)}_{index}"] = field_expression

        return result


if __name__ == "__main__":
    alpha_generator = AlphaFactorGenerator()
    alpha_factor_dict = alpha_generator.get_alpha_expression()
    with open(f"./alpha_360.json", "w") as f:
        json.dump(alpha_factor_dict, f)
