package Ejercicio_10;

import java.util.List;
import java.util.Objects;

public class ComplejoUnicoDeporte extends ComplejoDeportivo {
    private Deporte deporteExclusivo;

    public ComplejoUnicoDeporte(String localizacion, String jefeOrganizacion, double areaOcupada, 
                                List<AreaDesignada> areas, Deporte deporteExclusivo) {
        super(localizacion, jefeOrganizacion, areaOcupada, areas);
        Objects.requireNonNull(deporteExclusivo, "El deporte exclusivo no puede ser nulo en un complejo único");
        this.deporteExclusivo = deporteExclusivo;
    }

    public Deporte getDeporteExclusivo() {
        return deporteExclusivo;
    }

    public void setDeporteExclusivo(Deporte deporteExclusivo) {
        Objects.requireNonNull(deporteExclusivo, "El deporte exclusivo no puede ser nulo");
        this.deporteExclusivo = deporteExclusivo;
    }
}
