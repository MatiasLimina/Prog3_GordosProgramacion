package Ejercicio_10;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class Polideportivo extends ComplejoDeportivo {
    private List<Deporte> deportesAdmitidos;

    public Polideportivo(String localizacion, String jefeOrganizacion, double areaOcupada, 
                         List<AreaDesignada> areas, List<Deporte> deportesAdmitidos) {
        super(localizacion, jefeOrganizacion, areaOcupada, areas);
        Objects.requireNonNull(deportesAdmitidos, "La lista de deportes admitidos no puede ser nula");
        this.deportesAdmitidos = new ArrayList<>(deportesAdmitidos);
    }

    public void agregarDeporteAdmitido(Deporte deporte) {
        Objects.requireNonNull(deporte, "El deporte no puede ser nulo");
        if (!deportesAdmitidos.contains(deporte)) {
            deportesAdmitidos.add(deporte);
        }
    }

    public List<Deporte> getDeportesAdmitidos() {
        return Collections.unmodifiableList(deportesAdmitidos);
    }

    public void setDeportesAdmitidos(List<Deporte> deportesAdmitidos) {
        Objects.requireNonNull(deportesAdmitidos, "La lista de deportes no puede ser nula");
        this.deportesAdmitidos = new ArrayList<>(deportesAdmitidos);
    }
}
