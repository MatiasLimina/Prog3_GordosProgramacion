package Ejercicio_05;

import java.util.ArrayList;
import java.util.List;

public class Restaurante {
    private String nombre;
    private List<Sucursal> sucursales;
    private List<Plato> platosOfrecidos;

    public Restaurante(String nombre) {
        this.nombre = nombre;
        this.sucursales = new ArrayList<>();
        this.platosOfrecidos = new ArrayList<>();
    }

    public void agregarSucursal(Sucursal sucursal) {
        this.sucursales.add(sucursal);
    }

    // Agrega nuevos platos al restaurante hasta un máximo de 20
    public boolean agregarPlato(Plato plato) {
        if (this.platosOfrecidos.size() < 20) {
            this.platosOfrecidos.add(plato);
            return true;
        } else {
            System.out.println("Límite alcanzado: El restaurante " + this.nombre + " ya tiene 20 platos.");
            return false;
        }
    }

    public String getNombre() { return nombre; }
}
